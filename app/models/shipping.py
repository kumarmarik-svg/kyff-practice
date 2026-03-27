from app.extensions import db


class ShippingRule(db.Model):
    __tablename__ = "shipping_rules"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2), nullable=True)
    max_order_amount = db.Column(db.Numeric(10, 2), nullable=True)
    flat_rate = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    pincode_prefix = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    priority = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<ShippingRule {self.name}>"
