from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Model, CharField, SlugField, IntegerField, PositiveSmallIntegerField, DateTimeField, \
    ForeignKey, CASCADE, ImageField, CheckConstraint, Q, BooleanField, TextChoices, PositiveIntegerField, DateField, \
    TextField, EmailField, OneToOneField, JSONField, ManyToManyField, F, Sum
from django.utils.text import slugify
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field
from mptt.models import MPTTModel, TreeForeignKey


class CreatedBaseModel(Model):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class SlugBaseModel(Model):
    name = CharField(max_length=255)
    slug = SlugField(max_length=255, unique=True, editable=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)
        while self.__class__.objects.filter(slug=self.slug).exists():
            self.slug += '-1'

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class User(AbstractUser):
    pass

    @property
    def cart_count(self):
        return self.user_cart.count()


class SiteSettings(Model):
    tax = PositiveSmallIntegerField()

    def clean(self):
        if self.tax <= 0:
            raise ValidationError({'tax': 'Tax rate must be greater than zero.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return F"Tax: {self.tax}%"


class Category(SlugBaseModel, MPTTModel):
    parent = TreeForeignKey('self', CASCADE, blank=True, null=True, related_name='children')

    class MPTTMete:
        order_insertion_by = ["name"]


class Product(CreatedBaseModel):
    name = CharField(max_length=255)
    price = IntegerField()
    discount = PositiveIntegerField(default=0, db_default=0)
    quantity = PositiveIntegerField(default=0, db_default=0)
    shipping_cost = PositiveIntegerField(default=0)
    tags = ManyToManyField('apps.Tags', blank=True)
    category = ForeignKey('apps.Category', CASCADE, related_name='products')
    info = CKEditor5Field()
    specification = JSONField(default=dict)
    descriptions = CKEditor5Field()
    updated = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(discount__lte=100),
                name='discount__lte__100',
            )
        ]

    @property
    def is_new(self):
        return self.created_at >= now() - timedelta(days=7)

    @property
    def in_stock(self):
        return self.quantity > 0

    @property
    def current_price(self):
        return self.price - self.price * self.discount // 100

    @property
    def first_five(self):
        return list(self.specification.values())[:5]


class ProductImage(Model):
    image = ImageField(upload_to="product_images/")
    product = ForeignKey('apps.Product', CASCADE, related_name='images')

    def __str__(self):
        return f"Images for {self.product.name}"


class CartItem(Model):
    product = ForeignKey('apps.Product', CASCADE)
    user = ForeignKey('apps.User', CASCADE, related_name='user_cart')
    quantity = PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Review(Model):
    name = CharField(max_length=255)
    posted_at = DateField(auto_now_add=True)
    review_text = TextField()
    email_address = EmailField()
    product = ForeignKey('apps.Product', CASCADE)

    def __str__(self):
        return F'Review_NAME-{self.name},   Product_NAME-{self.product.name}'


class Favorite(Model):
    quantity = IntegerField()
    is_like = BooleanField(blank=True, null=True)
    user = ForeignKey('apps.User', CASCADE)
    product = ForeignKey('apps.Product', CASCADE, related_name='product_like')

    def __str__(self):
        return self.product.name


class Tags(Model):
    name = CharField(max_length=255, unique=True)
    slug = SlugField(max_length=255, editable=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)
        super().save(force_insert, force_update, update_fields, using)

    def __str__(self):
        return self.name


class Order(CreatedBaseModel):
    class Status(TextChoices):
        PROCESSING = 'processing', 'Processing'
        ON_HOLD = 'on_hold', 'On Hold'
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'

    class PaymentMethod(TextChoices):
        PAYPAL = 'paypal', 'PayPal'
        Credit_Card = 'credit_card', 'Credit Card'

    status = CharField(max_length=25, choices=Status.choices, default=Status.PROCESSING)
    payment_method = CharField(max_length=25, choices=PaymentMethod.choices)
    owner = ForeignKey('apps.User', CASCADE, related_name='orders')
    address = ForeignKey('apps.Address', CASCADE)

    def __str__(self):
        return f'Order {self.id} - {self.status}'

    @property
    def total(self):
        return (self.orderitem_set.aggregate(
            total=Sum(F('quantity') * (F('product__price') * (
                    100 - F('product__discount')) / 100)) + Sum(F('product__shipping_cost'))
        ))


class OrderItem(Model):
    product = ForeignKey('apps.Product', CASCADE)
    order = ForeignKey('apps.Order', CASCADE)
    quantity = PositiveIntegerField(default=1)

    @property
    def amount(self):
        return self.quantity * self.product.current_price


class Address(CreatedBaseModel):
    user = ForeignKey('apps.User', CASCADE, related_name='address')
    full_name = CharField(max_length=255)
    street = CharField(max_length=255)
    zip_code = PositiveIntegerField()
    city = CharField(max_length=255)
    phone = CharField(max_length=255)

    def __str__(self):
        return self.city


class CreditCard(CreatedBaseModel):
    order = OneToOneField('apps.Order', CASCADE)
    number = CharField(max_length=16)
    cvv = CharField(max_length=3)
    expire_date = DateField()
    owner = ForeignKey('apps.User', CASCADE)
