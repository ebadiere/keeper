# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lib.pymaker.pymaker import Address, zrx
from lib.pymaker.pymaker.numeric import Wad, Ray
from lib.pymaker.pymaker.oasis import SimpleMarket, Order
from lib.pymaker.pymaker.sai import Tub, Tap


class Conversion:
    def __init__(self, source_token: Address, target_token: Address, rate: Ray, max_source_amount: Wad, method: str):
        self.source_amount = None
        self.source_token = source_token
        self.target_amount = None
        self.target_token = target_token
        self.rate = rate
        self.max_source_amount = max_source_amount
        self.method = method

    def name(self):
        raise NotImplementedError("name() not implemented")

    def transact(self):
        raise NotImplementedError("transact() not implemented")

    def __str__(self):
        def amt(amount: Wad) -> str:
            return f"{amount} " if amount is not None else ""

        return f"[{amt(self.source_amount)}{self.source_token} -> {amt(self.target_amount)}{self.target_token} " \
               f"@{self.rate} by {self.method} (max={self.max_source_amount} {self.source_token})]"


class TubJoinConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.gem(),
                         target_token=self.tub.skr(),
                         rate=(Ray.from_number(1) / Ray(tub.ask(Wad.from_number(1)))),
                         max_source_amount=Wad.from_number(1000000),  #1 mio ETH = infinity ;)
                         method="tub.join()")

    def id(self):
        return f"tub.join()"

    def name(self):
        return f"tub.join('{self.source_amount}')"

    def transact(self):
        return self.tub.join(self.target_amount)


class TubExitConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.skr(),
                         target_token=self.tub.gem(),
                         rate=Ray(tub.bid(Wad.from_number(1))),
                         max_source_amount=Wad.from_number(1000000),  #1 mio SKR = infinity ;)
                         method="tub.exit()")

    def id(self):
        return f"tub.exit()"

    def name(self):
        return f"tub.exit('{self.source_amount}')"

    def transact(self):
        return self.tub.exit(self.source_amount)


class TubBoomConversion(Conversion):
    def __init__(self, tub: Tub, tap: Tap):
        self.tub = tub
        self.tap = tap
        super().__init__(source_token=self.tub.skr(),
                         target_token=self.tub.sai(),
                         rate=Ray(tap.bid(Wad.from_number(1))),
                         max_source_amount=self.boomable_amount_in_skr(tap),
                         method="tub.boom()")

    #TODO currently the keeper doesn't see `joy` changing unless `drip` gets called
    #this is the thing `sai-explorer` is trying to calculate on his own
    def boomable_amount_in_sai(self, tap: Tap):
        return Wad.max(tap.joy() - tap.woe(), Wad.from_number(0))

    def boomable_amount_in_skr(self, tap: Tap):
        # we deduct 0.000001 in order to avoid rounding errors
        return Wad.max(Wad(self.boomable_amount_in_sai(tap) / (tap.bid(Wad.from_number(1)))) - Wad.from_number(0.000001), Wad.from_number(0))

    def id(self):
        return f"tub.boom()"

    def name(self):
        return f"tub.boom('{self.source_amount}')"

    def transact(self):
        return self.tap.boom(self.source_amount)


class TubBustConversion(Conversion):
    def __init__(self, tub: Tub, tap: Tap):
        self.tub = tub
        self.tap = tap
        super().__init__(source_token=self.tub.sai(),
                         target_token=self.tub.skr(),
                         rate=(Ray.from_number(1) / Ray(tap.ask(Wad.from_number(1)))),
                         max_source_amount=self.bustable_amount_in_sai(tap),
                         method="tub.bust()")

    def bustable_amount_in_sai(self, tap: Tap):
        #TODO we always try to bust 10 SAI less than what the Tub reports
        #in order to discount the growth of `joy()` that might've have happened since the last drip
        #of course this is not the right solution and it won't even work properly if the last
        #drip happened enough time ago
        bustable_woe = tap.woe() - tap.joy() - Wad.from_number(10)

        # we deduct 0.000001 in order to avoid rounding errors
        bustable_fog = tap.fog() * tap.ask(Wad.from_number(1)) - Wad.from_number(0.000001)

        return Wad.max(bustable_woe, bustable_fog, Wad.from_number(0))

    def id(self):
        return f"tub.bust()"

    def name(self):
        return f"tub.bust('{self.target_amount}')"

    def transact(self):
        return self.tap.bust(self.target_amount)


class OasisTakeConversion(Conversion):
    def __init__(self, otc: SimpleMarket, order: Order):
        self.otc = otc
        self.order = order
        super().__init__(source_token=order.buy_token,
                         target_token=order.pay_token,
                         rate=Ray(order.pay_amount) / Ray(order.buy_amount),
                         max_source_amount=order.buy_amount,
                         method=f"otc.take({self.order.order_id})")

    def id(self):
        return f"otc.take({self.order.order_id})"

    def name(self):
        return f"otc.take({self.order.order_id}, '{self.quantity()}')"

    def transact(self):
        return self.otc.take(self.order.order_id, self.quantity())

    def quantity(self):
        quantity = self.target_amount

        #TODO probably at some point dust order limitation will get introuced at the contract level
        #if that happens, a concept of `min_source_amount` will be needed

        # if by any chance rounding makes us want to buy more quantity than is available,
        # we just buy the whole lot
        if quantity > self.order.pay_amount:
            quantity = self.order.pay_amount

        # if by any chance rounding makes us want to buy only slightly less than the available lot,
        # we buy everything as this is probably what we wanted in the first place
        if self.order.pay_amount - quantity < Wad.from_number(0.0000000001):
            quantity = self.order.pay_amount

        return quantity


class ZrxFillOrderConversion(Conversion):
    def __init__(self, exchange: zrx.ZrxExchange, order: zrx.Order):
        self.exchange = exchange
        self.order = order

        super().__init__(source_token=order.buy_token,
                         target_token=order.pay_token,
                         rate=Ray(order.pay_amount) / Ray(order.buy_amount),
                         max_source_amount=order.buy_amount - self.exchange.get_unavailable_buy_amount(self.order),
                         method=f"zrx.fill_order({hash(self.order)})")

    def id(self):
        return f"zrx.fill_order({hash(self.order)})"

    def name(self):
        return f"zrx.fill_order({hash(self.order)}, '{self.quantity()}')"

    def transact(self):
        return self.exchange.fill_order(self.order, self.quantity())

    def quantity(self):
        quantity = self.source_amount

        # if by any chance rounding makes us want to sell more quantity than is possible,
        # we just buy the whole lot
        if quantity > self.order.buy_amount:
            quantity = self.order.buy_amount

        # if by any chance rounding makes us want to buy only slightly less than the possible lot,
        # we buy everything as this is probably what we wanted in the first place
        if self.order.buy_amount - quantity < Wad.from_number(0.0000000001):
            quantity = self.order.buy_amount

        return quantity
