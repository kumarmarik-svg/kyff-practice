from app.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=True)
    rating = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(150), nullable=True)
    body = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_verified_purchase = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("product_id", "user_id", name="uq_review_product_user"),
    )

    order_item = db.relationship("OrderItem", lazy=True)

    def __repr__(self):
        return f"<Review product_id={self.product_id} rating={self.rating}>"
