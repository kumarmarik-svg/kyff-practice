from app.models import Review


class TestCategories:
    def test_list_empty(self, client):
        res = client.get("/api/categories/")
        assert res.status_code == 200
        assert res.get_json()["data"] == []

    def test_list_with_category(self, client, category):
        res = client.get("/api/categories/")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_get_by_slug(self, client, category):
        res = client.get(f"/api/categories/{category.slug}")
        assert res.status_code == 200
        assert res.get_json()["data"]["slug"] == category.slug

    def test_get_not_found(self, client):
        assert client.get("/api/categories/nonexistent").status_code == 404


class TestProducts:
    def test_list_empty(self, client):
        res = client.get("/api/products/")
        assert res.status_code == 200
        assert res.get_json()["data"]["total"] == 0

    def test_list_with_product(self, client, product):
        res = client.get("/api/products/")
        assert res.status_code == 200
        assert res.get_json()["data"]["total"] == 1

    def test_featured(self, client, product):
        res = client.get("/api/products/featured")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_search_hit(self, client, product):
        res = client.get("/api/products/search?q=rice")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_search_miss(self, client, product):
        res = client.get("/api/products/search?q=zzznomatch")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 0

    def test_search_no_query(self, client):
        assert client.get("/api/products/search").status_code == 400

    def test_get_by_slug(self, client, product):
        res = client.get(f"/api/products/{product.slug}")
        assert res.status_code == 200
        d = res.get_json()["data"]
        assert d["slug"] == product.slug
        assert "variants" in d
        assert "images" in d

    def test_get_not_found(self, client):
        assert client.get("/api/products/nonexistent").status_code == 404

    def test_filter_by_category(self, client, product, category):
        res = client.get(f"/api/products/?category={category.slug}")
        assert res.status_code == 200
        assert res.get_json()["data"]["total"] == 1

    def test_product_with_variant(self, client, product_with_variant):
        p, v = product_with_variant
        res = client.get(f"/api/products/{p.slug}")
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["has_variants"] is True
        assert len(data["variants"]) == 1
        assert data["variants"][0]["sku"] == v.sku


class TestProductReviews:
    def test_no_reviews(self, client, product):
        res = client.get(f"/api/products/{product.slug}/reviews")
        assert res.status_code == 200
        assert res.get_json()["data"]["total"] == 0

    def test_only_approved_reviews_shown(self, client, db, product, user):
        db.session.add(Review(
            product_id=product.id, user_id=user.id,
            rating=5, is_approved=False,
        ))
        db.session.commit()
        res = client.get(f"/api/products/{product.slug}/reviews")
        assert res.get_json()["data"]["total"] == 0

    def test_approved_review_shown(self, client, db, product, user):
        db.session.add(Review(
            product_id=product.id, user_id=user.id,
            rating=4, title="Great", is_approved=True,
        ))
        db.session.commit()
        res = client.get(f"/api/products/{product.slug}/reviews")
        assert res.get_json()["data"]["total"] == 1
