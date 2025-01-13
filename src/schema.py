from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)
from typing_extensions import Annotated


def validate_url(url: str) -> str:
    """Validate and normalize URL string."""
    # Add HTTPS scheme if missing
    if "://" not in url:
        url = "https://" + url
    try:
        # Validate URL using Pydantic's HttpUrl
        parsed = HttpUrl(url)
        return str(parsed)
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")


# Replace the existing HttpUrlString definition
HttpUrlString = Annotated[str, AfterValidator(validate_url)]


class Category(BaseModel):
    name: str
    url: Optional[str] = None


class ContextEnum(str, Enum):
    SCHEMA_ORG_HTTPS = "https://schema.org/"
    SCHEMA_ORG_HTTP = "http://schema.org/"
    SCHEMA_ORG_HTTPS_NO_SLASH = "https://schema.org"
    SCHEMA_ORG_HTTP_NO_SLASH = "http://schema.org"


class VideoObject(BaseModel):
    context: ContextEnum = Field(
        ...,
        validation_alias="@context",
    )
    type: str = Field(..., validation_alias="@type", pattern="VideoObject")
    name: str = Field(..., description="The name of the video.")
    description: Optional[str] = Field(
        default=None, description="The description of the video."
    )
    thumbnailUrl: Optional[List[HttpUrlString]] = Field(
        default=None, description="A URL pointing to the video thumbnail image."
    )
    uploadDate: Optional[datetime] = Field(
        default=None, description="The date when the video was uploaded."
    )
    duration: Optional[str] = Field(
        default=None, description="The duration of the video in ISO 8601 format."
    )
    contentUrl: Optional[HttpUrlString] = Field(
        default=None, description="A URL pointing to the actual video content."
    )
    embedUrl: Optional[HttpUrlString] = Field(
        default=None, description="A URL pointing to a player for the video."
    )
    interactionCount: Optional[int] = Field(
        default=None, description="The number of interactions for the video."
    )

    model_config = ConfigDict(populate_by_name=True)  # Allow using aliases


class CustomAttribute(BaseModel):
    text: Optional[List[str]] = Field(default=None, description="Text attributes")
    numbers: Optional[List[float]] = Field(
        default=None, description="Number attributes"
    )


class Interval(BaseModel):
    # Assuming Interval is a model with fields like min_value and max_value.
    # These would need to be properly defined based on the Protobuf definition of Interval.
    min_value: Optional[float]
    max_value: Optional[float]


class PriceRange(BaseModel):
    price: Optional[Interval] = Field(
        default=None, description="Price interval of all variant products."
    )
    original_price: Optional[Interval] = Field(
        default=None, description="Original price interval of all variant products."
    )


class PriceInfo(BaseModel):
    currency_code: str = Field(..., description="3-letter ISO currency code.")
    price: float = Field(..., description="Price of the product.")
    original_price: Optional[float] = Field(
        default=None, description="Original price without discount."
    )
    cost: Optional[float] = Field(
        default=None, description="Cost of the product used for gross profit reporting."
    )
    price_effective_time: Optional[datetime] = Field(
        default=None, description="Timestamp when the price becomes effective."
    )
    price_expire_time: Optional[datetime] = Field(
        default=None, description="Timestamp when the price stops being effective."
    )
    price_range: Optional[PriceRange] = Field(
        default=None, description="Price range of variant products."
    )


class RatingTypeEnum(str, Enum):
    AGGREGATE_RATING = "AggregateRating"
    RATING = "Rating"


class Rating(BaseModel):
    type: Optional[RatingTypeEnum] = Field(default=None, validation_alias="@type")
    rating_count: Optional[int] = Field(
        default=None,
        # ge=0,
        description="Total number of ratings. Must be nonnegative.",
        validation_alias="ratingCount",
    )
    average_rating: Optional[float] = Field(
        default=None,
        ge=1,
        le=5,
        description="Average rating, scaled between 1-5.",
        validation_alias="ratingValue",
    )
    rating_histogram: Optional[List[int]] = Field(
        default=None, description="List of rating counts per rating value."
    )


class FulfillmentInfo(BaseModel):
    type: str = Field(
        ...,
        description="Fulfillment type such as 'pickup-in-store', 'same-day-delivery', or a custom type.",
        pattern=r"^(pickup-in-store|ship-to-store|same-day-delivery|next-day-delivery|custom-type-\d)$",
    )
    place_ids: List[str] = Field(
        ...,
        max_length=3000,
        description="Store or region IDs for the fulfillment type. Must match the pattern '[a-zA-Z0-9_-]'.",
        pattern=r"^[a-zA-Z0-9_-]{1,30}$",
    )


class Image(BaseModel):
    url: HttpUrlString = Field(
        description="Required. URI of the image. Must be a valid UTF-8 encoded URI with a maximum length of 5000 characters.",
    )
    height: Optional[int] = Field(
        default=None, description="Height of the image in pixels. Must be nonnegative."
    )
    width: Optional[int] = Field(
        default=None, description="Width of the image in pixels. Must be nonnegative."
    )


class Audience(BaseModel):
    genders: List[str] = Field(
        ...,
        max_length=5,
        description="The genders of the audience. Suggested values: 'male', 'female', 'unisex'. Maximum 5 values.",
    )
    age_groups: List[str] = Field(
        ...,
        max_length=5,
        description="The age groups of the audience. Suggested values: 'newborn', 'infant', 'toddler', 'kids', 'adult'. Maximum 5 values.",
    )


class ColorInfo(BaseModel):
    color_families: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        description="Standard color families, such as 'Red', 'Green', 'Blue'. Maximum 5 values.",
    )
    colors: Optional[List[str]] = Field(
        default=[],
        max_length=75,
        description="Color display names, which may differ from standard color family names. Maximum 75 values.",
    )


class Promotion(BaseModel):
    promotion_id: str


class Item(BaseModel):
    id_: HttpUrlString = Field(...)  # Use alias for @id
    name: str


class ItemList(BaseModel):
    context: ContextEnum = Field(
        ...,
    )
    type: str = Field(..., pattern="ItemList")
    itemListElement: List[Item]

    model_config = ConfigDict(populate_by_name=True)  # Allow using aliases


class BreadcrumbItem(BaseModel):
    type_: str = Field(..., pattern="ListItem")
    position: int
    item: "Item"


class BreadcrumbList(BaseModel):
    context: ContextEnum = Field(
        ...,
    )
    type_: str = Field(..., pattern="BreadcrumbList")
    itemListElement: List[BreadcrumbItem]


class PostalAddress(BaseModel):
    """Schema.org model for PostalAddress."""

    type: str = Field(default="PostalAddress", validation_alias="type")
    streetAddress: Optional[str]
    addressLocality: Optional[str]
    addressRegion: Optional[str]
    postalCode: Optional[str]
    addressCountry: Optional[str]


class ContactPoint(BaseModel):
    """Schema.org model for ContactPoint."""

    type: str = Field(default="ContactPoint", validation_alias="type")
    telephone: Optional[str]
    email: Optional[str]
    contactType: Optional[str] = "customer service"
    address: Optional[PostalAddress]


class Organization(BaseModel):
    """Schema.org model for Organization."""

    context: Optional[str] = Field(
        default="https://schema.org", validation_alias="context"
    )
    type: Optional[str] = Field(default="Organization", validation_alias="type")
    name: Optional[str]
    url: Optional[HttpUrlString]
    logo: Optional[HttpUrlString]
    contactPoint: Optional[ContactPoint]
    sameAs: Optional[List[HttpUrlString]]

    model_config = ConfigDict(
        populate_by_name=True
    )  # Allow use of aliases when populating models


class Brand(BaseModel):
    """
    Schema.org Brand definition.
    """

    type_: Optional[str] = Field(default="Brand", validation_alias="@type")
    name: Optional[str] = Field(..., description="The name of the brand.")
    logo: Optional[HttpUrlString] = Field(
        default=None, description="URL of the brand's logo."
    )
    url: Optional[HttpUrlString] = Field(
        default=None, description="The brand's official website."
    )
    description: Optional[str] = Field(
        default=None, description="Description of the brand."
    )
    sameAs: Optional[List[HttpUrlString]] = Field(
        default=None, description="URLs to external references for the brand."
    )

    model_config = ConfigDict(
        populate_by_name=True
    )  # Allow use of aliases when populating models


class Offer(BaseModel):
    """Schema.org Offer model."""

    type_: str = Field(default="Offer", validation_alias="@type")
    name: Optional[str] = Field(default=None, description="Name of the offer.")
    price: float = Field(..., description="Price of the offer.")
    priceCurrency: str = Field(..., description="Currency of the price.")
    sku: Optional[str] = Field(default=None, description="SKU of the product.")
    availability: Optional[HttpUrlString] = Field(
        default=None, description="Availability of the product."
    )
    itemCondition: Optional[HttpUrlString] = Field(
        default=None, description="Condition of the item."
    )
    seller: Optional[Organization] = Field(
        default=None, description="Seller offering the item."
    )

    model_config = ConfigDict(
        populate_by_name=True
    )  # Allow use of aliases when populating models


class Offers(BaseModel):
    """Wrapper class for a list of offers."""

    offers: Optional[List[Offer]] = Field(
        None, description="A list of individual offers for the product."
    )
    url: Optional[HttpUrlString] = Field(
        None, description="The URL where the product can be purchased."
    )
    itemCondition: Optional[str] = Field(
        None,
        description="The condition of the product (e.g., NewCondition, UsedCondition).",
    )


class AggregateOffer(BaseModel):
    """Schema.org AggregateOffer model."""

    type_: str = Field(default="AggregateOffer", validation_alias="@type")
    offerCount: Optional[int] = Field(None, description="Number of offers.")
    highPrice: Optional[float] = Field(None, description="Highest price of the offers.")
    lowPrice: Optional[float] = Field(None, description="Lowest price of the offers.")
    priceCurrency: str = Field(..., description="Currency of the offers.")
    itemCondition: Optional[HttpUrlString] = Field(
        None, description="Condition of the items."
    )
    seller: Optional[Organization] = Field(None, description="Seller organization.")
    offers: Optional[List[Offer]] = Field(
        None, description="List of individual offers."
    )

    model_config = ConfigDict(
        populate_by_name=True
    )  # Allow use of aliases when populating models


# REVIEWS
class Person(BaseModel):
    """Schema.org Person definition."""

    type_: str = Field(default="Person", validation_alias="@type")
    name: Optional[str] = Field(description="The name of the person.")


class Review(BaseModel):
    """Schema.org Review definition."""

    type_: str = Field(default="Review", validation_alias="@type")
    author: Person = Field(default=None, description="The author of the review.")
    datePublished: date = Field(
        default=None, description="The date the review was published."
    )
    reviewBody: Optional[str] = Field(
        default=None, description="The body of the review."
    )
    reviewRating: Rating = Field(
        default=None, description="The rating given in this review."
    )


class MediaObject(BaseModel):
    """Schema.org MediaObject model."""

    context: str = Field(default="https://schema.org", validation_alias="@context")
    type_: str = Field(default="MediaObject", validation_alias="@type")
    contentUrl: Optional[HttpUrl] = Field(
        None, description="URL to the actual content of the media object."
    )
    encodingFormat: Optional[str] = Field(
        None, description="The media format or mime type."
    )
    uploadDate: Optional[datetime] = Field(
        None, description="The date the media was uploaded."
    )
    name: Optional[str] = Field(None, description="The name of the media object.")


class CreativeWork(MediaObject):
    """Schema.org CreativeWork model."""

    author: Optional[str] = Field(None, description="Author of the work.")
    license: Optional[HttpUrl] = Field(
        None, description="License under which the work is published."
    )
    datePublished: Optional[datetime] = Field(
        None, description="Date of first publication."
    )


class ThreeDModel(CreativeWork):
    """Schema.org 3DModel model."""

    type_: str = Field(default="3DModel", validation_alias="@type")
    creator: Optional[str] = Field(None, description="The creator of the 3D model.")
    contentSize: Optional[str] = Field(
        None, description="File size in megabytes or gigabytes."
    )
    material: Optional[str] = Field(
        None, description="The material used to create the 3D model."
    )
    embedUrl: Optional[HttpUrl] = Field(
        None, description="A URL pointing to a player for the 3D model."
    )
    thumbnailUrl: Optional[List[HttpUrl]] = Field(
        None, description="A URL pointing to the model thumbnail image."
    )
    encodingFormat: Optional[str] = Field(
        None, description="The file format of the 3D model (e.g., 'model/gltf+json')."
    )
    isBasedOnUrl: Optional[HttpUrl] = Field(
        None, description="A related resource that the 3D model is based on."
    )
    interactionCount: Optional[int] = Field(
        None, description="Number of interactions for the 3D model."
    )
    encoding: Optional[List[MediaObject]] = Field(
        None,
        description="A media object representing the 3D model.",
    )

    model_config = ConfigDict(
        populate_by_name=True
    )  # Allow use of aliases when populating models


class Product(BaseModel):
    """FKA - Formerly Known as Extracted Product"""

    id: Optional[str] = Field(default=None, description="Product identifier.")
    catalog: Optional[str] = Field(
        default=None,
        description="Catalog name, or ecommerce site name. Eg: Macys, sephora etc",
    )
    url: Optional[HttpUrlString] = Field(
        default=None, description="Canonical URL linking to the product detail page."
    )
    name: Optional[str] = Field(
        default=None, description="Full name or title of the product."
    )

    # Type of the product.
    type: Optional[str] = Field(
        default="Product", description="The schema type.", alias="@type"
    )

    # Used by Variant to refer to the productGroupID of the productGroup in which the product belongs.
    primary_product_id: Optional[str] = Field(
        default=None,
        description="Used by Variant to refer to the productGroupID of the productGroup in which the product belongs",
    )
    description: Optional[str] = Field(default=None, description="Product description.")
    # Global Trade Item Numbers.
    # Schema.org property
    # [Product.isbn](https:#schema.org/isbn),
    # [Product.gtin8](https://schema.org/gtin8),
    # [Product.gtin12](https://schema.org/gtin12),
    # [Product.gtin13](https://schema.org/gtin13),
    # [Product.gtin14](https://schema.org/gtin14).
    gtin: Optional[str] = Field(default=None, description="Global Trade Item Number.")

    # Product categories. This field is a list for supporting one product
    # belonging to several parallel categories.
    #
    # For example, if a shoes product belongs to both
    # ["Shoes & Accessories" -> "Shoes"] and
    # ["Sports & Fitness" -> "Athletic Clothing" -> "Shoes"], it could be
    # represented as:
    #
    #      "categories": [
    #        "Shoes & Accessories > Shoes",
    #        "Sports & Fitness > Athletic Clothing > Shoes"
    #      ]
    # Some catalogs have an optional url field that renders the cataegory page.
    categories: Optional[List[Category]] = Field(
        default=None, description="Product categories."
    )

    # Schema.org property [Product.brand](https://schema.org/brand)
    brand: Optional[Union[Brand, Organization]] = Field(
        default=None,
        description="The brand or organization associated with the product.",
    )
    language_code: Optional[str] = Field(
        default="en-US", description="Language of the name and description."
    )

    # Extra product attributes to be included. For example,
    # for products, this could include the store name, vendor, style, color, etc.
    # These can be used in facets as well as to provide features for search.
    #
    # Features that can take on one of a limited number of possible values. Two
    # types of features can be set are:
    #
    # Textual features. some examples would be the brand/maker of a product, or
    # country of a customer. Numerical features. Some examples would be the
    # height/weight of a product, or age of a customer.
    #
    # For example:
    # `{
    #   "vendor": {"text": ["vendor123", "vendor456"]},
    #   "lengths_cm": {"numbers":[2.3, 15.4]},
    #   "heights_cm": {"numbers":[8.1, 6.4]}
    # }`.
    addtional_attributes: Optional[Dict[str, CustomAttribute]] = Field(
        default=None, description="Extra product attributes."
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Custom tags associated with the product."
    )
    price_info: Optional[PriceInfo] = Field(
        default=None, description="Product price and cost information."
    )
    rating: Optional[Rating] = Field(
        default=None, description="Product rating.", validation_alias="aggregateRating"
    )
    # We are referring to the schema.org property [Product.image](https://schema.org/image) but with a list of images since some products contain multiple images.
    images: Optional[List[Image]] = Field(default=None, description="Product image.")
    # The primary image of the product is used for display purposes.
    image: Optional[Image] = Field(default=None, description="Primary product image.")

    class AvailabilityEnum(str, Enum):
        AVAILABILITY_UNSPECIFIED = "AVAILABILITY_UNSPECIFIED"
        IN_STOCK = "IN_STOCK"
        OUT_OF_STOCK = "OUT_OF_STOCK"
        PREORDER = "PREORDER"
        BACKORDER = "BACKORDER"

    available_time: Optional[datetime] = Field(
        default=None, description="Timestamp when the product becomes available."
    )
    availability: Optional[AvailabilityEnum] = Field(
        default=AvailabilityEnum.IN_STOCK, description="Product availability."
    )
    available_quantity: Optional[int] = Field(
        default=None, description="Available quantity of the item."
    )
    fulfillment_info: Optional[List[FulfillmentInfo]] = Field(
        default=None, description="Fulfillment information."
    )
    audience: Optional[Audience] = Field(
        default=None, description="Target group associated with the product."
    )
    color_info: Optional[ColorInfo] = Field(
        default=None, description="Color of the product."
    )
    sizes: Optional[List[str]] = Field(default=None, description="Size of the product.")
    materials: Optional[List[str]] = Field(
        default=None, description="Material of the product."
    )
    patterns: Optional[List[str]] = Field(
        default=None, description="Pattern or graphic print of the product."
    )
    promotions: Optional[List[Promotion]] = Field(
        default=None, description="Promotions applied to the product."
    )

    breadcrumbList: Optional[BreadcrumbList] = Field(
        default=None, description="Breadcrumb list of the product."
    )

    organization: Optional[Organization] = Field(
        default=None,
        description="Organization details.",
        validation_alias="corporation",
    )

    offers: Optional[Union[Offer, AggregateOffer, Offers]] = Field(
        default=None, description="Offer or AggregateOffer for the product."
    )

    extra_text: Optional[str] = Field(
        default=None,
        description="Extra text field for additional information. Extracted from the web-page",
    )

    review: Optional[List[Review]] = Field(
        # the alias is "reviews" because that is what a lot of brands use. Schema.org says "reviews" has been superseded by "review"
        default=None,
        description="List of reviews for the product.",
        validation_alias="reviews",
    )

    three_d_model: Optional[List[ThreeDModel]] = Field(
        default=None,
        description="3D model of the product.",
        validation_alias="3dModel",
    )

    def get_defined_fields(self) -> List[str]:
        return [field for field, value in self.__dict__.items() if value is not None]

    def get_undefined_fields(self) -> List[str]:
        return [field for field, value in self.__dict__.items() if value is None]

    def serialize_for_parquet(self, by_alias: bool) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias)

    @classmethod
    def deserialize_from_parquet(cls, row: Any) -> "Product":
        """Instantiate a Product object from a row of a parquet file."""
        return cls(**deserialize_row(row))

    def __str__(self) -> str:
        # Filter attributes, excluding any that contain "embedding" in their name
        # filtered_attributes = {
        #     k: v
        #     for k, v in self.model_dump().items()
        #     if "embedding" not in k and k != "extra_etext"
        # }
        # Convert all attributes to native types
        # serialized_attributes = to_native_type(filtered_attributes)
        # Use yaml.safe_dump to print in clean YAML format
        # return yaml.safe_dump(
        # serialized_attributes, default_flow_style=False, sort_keys=False
        # )
        # return json.dumps(serialized_attributes, indent=2)
        return yaml.safe_dump(
            yaml.safe_load(
                self.model_dump_json(indent=2, exclude_none=True, exclude_unset=True)
            ),
            default_flow_style=False,
            sort_keys=False,
        )


class ProductGroup(Product):
    productGroupID: Optional[str] = Field(
        default=None, description="ID of the product group."
    )
    variesBy: Optional[List[HttpUrlString]] = Field(
        default=None,
        description="Indicates the property or properties by which the variants in a ProductGroup vary, e.g. their size, color, etc.",
    )
    hasVariant: Optional[List[Product]] = Field(
        default=None,
        description="Indicates a list of Products that are variants of this ProductGroup",
    )

    @classmethod
    def deserialize_from_parquet(cls, row: Any) -> "ProductGroup":
        """Instantiate a Product object from a row of a parquet file."""
        return cls(**deserialize_row(row))

    def __hash__(self) -> int:
        """Make ProductGroup hashable based on productGroupID."""
        if self.url is None:
            raise ValueError("Cannot hash ProductGroup without url")
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        """Implement equality check for hash consistency."""
        if not isinstance(other, ProductGroup):
            return NotImplemented
        if self.url is None or other.url is None:
            return False
        return self.url == other.url
