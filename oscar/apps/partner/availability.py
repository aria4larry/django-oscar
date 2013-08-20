from django.utils.translation import ugettext_lazy as _


class Base(object):
    """
    Simple based availability class which defaults to everything being
    unavailable.
    """

    # Standard properties
    code = ''
    message = ''
    lead_time = None
    dispatch_date = None

    @property
    def is_available_to_buy(self):
        """
        Test if this product is available to be bought.
        """
        # We test a purchase of a single item
        return self.is_purchase_permitted(1)[0]

    def is_purchase_permitted(self, quantity):
        """
        Test whether a proposed purchase is allowed

        Should return a boolean and a reason
        """
        return False, _("Unavailable")


# Common availability policies


class Unavailable(Base):
    """
    Policy for when a product is unavailable
    """
    code = 'unavailable'
    message = _("Unavailable")


class Available(Base):
    """
    For when a product is always available, irrespective of stocklevel.

    This might be appropriate for a digital product.
    """
    code = 'available'
    message = _("Available")

    def is_purchase_permitted(self, quantity):
        return True, ""


class StockRequired(Base):
    """
    Ensure that the num_in_stock field of the stockrecord is
    respected.
    """
    CODE_IN_STOCK = 'instock'
    CODE_OUT_OF_STOCK = 'outofstock'

    def __init__(self, stockrecord=None):
        self.stockrecord = stockrecord

    def is_purchase_permitted(self, quantity):
        num_in_stock = self.stockrecord.net_stock_level
        if num_in_stock == 0:
            return False, _("No stock available")
        if quantity > num_in_stock:
            msg = _("A maximum of %(max)d can be bought") % {
                'max': num_in_stock}
            return False, msg
        return True, ""

    @property
    def code(self):
        if self.stockrecord.net_stock_level > 0:
            return self.CODE_IN_STOCK
        return self.CODE_OUT_OF_STOCK

    @property
    def message(self):
        if self.stockrecord.net_stock_level > 0:
            return _("In stock (%d available)") % self.stockrecord.net_stock_level
        return _("Not available")


class DelegateToStockRecord(Base):
    """
    An availability class which delegates all calls to the
    stockrecord itself.  This will exercise the deprecate methods on the
    stockrecord that call "partner wrapper" classes.
    """

    def __init__(self, product, stockrecord=None, user=None):
        self.product = product
        self.stockrecord = stockrecord
        self.user = user

    @property
    def is_available_to_buy(self):
        if self.stockrecord is None:
            return False
        if not self.product.get_product_class().track_stock:
            return True
        return self.stockrecord.is_available_to_buy

    def is_purchase_permitted(self, quantity):
        return self.stockrecord.is_purchase_permitted(
            self.user, quantity, self.product)

    @property
    def code(self):
        return self.stockrecord.availability_code

    @property
    def message(self):
        return self.stockrecord.availability

    @property
    def lead_time(self):
        return self.stockrecord.lead_time

    @property
    def dispatch_date(self):
        return self.stockrecord.dispatch_date