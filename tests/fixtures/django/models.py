import logging
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models  # type: ignore
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from finance_engine_sdk.enums import FinanceEngineVersion
from model_utils.models import TimeStampedModel  # type: ignore
from pj_django_payments.models import AuditableModel, FinancialProduct, Payment
from pj_six_sdk.enums import Status
from pj_six_sdk.schemas import CreateOrderRequests
from pj_six_sdk.schemas import CustomerInfoSchema as SixCustomerInfoSchema

from six_payment_provider.six.enums import FEStatus, MetadataKeys
from six_payment_provider.six.exceptions import SixException

logger = logging.getLogger(__name__)


def get_metadata_default_dict() -> dict[str, Any]:
    """Default dictionary to keep track of changes in state. Add a dictionary containing the date the state
    changed. For example:
    metadata["state_changes"][PaymentState.PAID.value].append({"date":"2022-08-08T15:45:00+00:00"}).
    """
    metadata = dict()
    metadata[MetadataKeys.STATE_CHANGES.value] = dict()
    metadata[MetadataKeys.STATE_CHANGES.value][Status.PENDING_PAYMENT.value] = []
    metadata[MetadataKeys.STATE_CHANGES.value][Status.EXPIRED.value] = []
    metadata[MetadataKeys.STATE_CHANGES.value][Status.PAID.value] = []
    return metadata


class SixPaymentOrder(AuditableModel, TimeStampedModel):
    """Model to store the reference request sent from finance engine."""

    # STATUS_CHOICES = ((status.name, status.value) for status in Status)
    STATUS_CHOICES = (
        ("PENDING_PAYMENT", _("Pending_payment")),
        ("PAID", _("Paid")),
        ("EXPIRED", _("Expired")),
    )
    FE_STATUS_CHOICES = ((status.name, status.value) for status in FEStatus)
    amount = models.DecimalField(
        _("Amount"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Amount to paid in reference."),
    )
    metadata = models.JSONField(
        _("Metadata"),
        default=get_metadata_default_dict,
        help_text=_(
            "Metadata for the payment. It includes the dates with"
            " the changes of state. Please use the keys in enums.MetadataKeys."
        ),
        encoder=DjangoJSONEncoder,
    )

    date_received = models.DateTimeField(
        _("Date received"),
        null=True,
        blank=True,
        help_text=_("Date the callback was received from Six"),
    )
    date_paid = models.IntegerField(
        _("Date paid"),
        null=True,
        blank=True,
        help_text=_("Date the payment was received by Six"),
        db_index=True,
    )
    valid_through = models.IntegerField(
        _("Valid through date"),
        null=True,
        help_text=_("Date the reference is valid through"),
    )
    reference = models.CharField(
        _("Reference"),
        max_length=100,
        null=True,
        help_text=_("Reference for the payment"),
        db_index=True,
    )
    upc = models.CharField(
        _("UPC"),
        max_length=100,
        null=True,
        help_text=_("Unique service code"),
        db_index=True,
    )
    order_id = models.CharField(
        _("Order Id"),
        max_length=100,
        null=True,
        help_text=_("Order identifier for the payment"),
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=24,
        choices=STATUS_CHOICES,
        default=Status.PENDING_PAYMENT.value,
    )
    fe_status = models.CharField(
        _("FE Status"),
        max_length=24,
        choices=FE_STATUS_CHOICES,
        default=FEStatus.PENDING_PAYMENT.value,
    )

    fe_payment = models.ForeignKey(
        Payment,
        related_name="six_order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    financial_product = models.ForeignKey(FinancialProduct, on_delete=models.PROTECT, null=True, blank=True)

    def to_create_six_order(self) -> CreateOrderRequests:
        """Creates the Six Order object from the information in the model.
        :return: an CreateOrderRequests Object with the information in the model.
        """
        if self.financial_product is None:
            raise SixException("To create a CreateOrderRequest financial prodcut cannot be None.")

        if (
            self.valid_through is None
            and self.financial_product.finance_engine_version == FinanceEngineVersion.FEv2.value
        ):
            raise ValueError("valid_through is required for FEv2")

        if self.financial_product.customer is None:
            error_message = (
                "Cannot create a SIX order if the financial product customer is none. "
                f"Financial product id {self.financial_product.financial_product_id}"
            )
            raise SixException(error_message)

        customer_info: SixCustomerInfoSchema = SixCustomerInfoSchema(
            name=self.financial_product.customer.customer_fullname(),
            email=self.financial_product.customer.email,
            phone=self.financial_product.customer.device_phone_number,
        )
        create_order_requests: CreateOrderRequests = CreateOrderRequests(
            currency=self.financial_product.currency,
            total=int(self.amount * 100),  # Six is handled in cents and Fe units
            merchant_ref_id=self.financial_product.financial_product_id,
            expires_at=self.valid_through,
            customer_info=customer_info,
        )
        return create_order_requests

    def update_metadata(self, data: dict, status: Status | None = None) -> None:
        """Updates the metadata with the date sent/recive to SIX
        :return:
        """
        to_status = status if status else self.status
        self.metadata[MetadataKeys.STATE_CHANGES.value][to_status].append(
            {"date_event": timezone.now().strftime("%Y-%m-%d %H:%M:%S"), "data": data}
        )


class SixReconciliationPayment(TimeStampedModel):
    """This model represents a recods file of Six."""

    report_date = models.DateField()
    payment_date = models.DateTimeField()
    authorization_number = models.PositiveBigIntegerField()
    reference = models.CharField(max_length=40, db_index=True)
    sku = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_number = models.CharField(max_length=36, db_index=True, unique=True)
