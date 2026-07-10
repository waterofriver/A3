def test_openapi_includes_normalized_error_envelope(client):
    schemas = client.app.openapi()["components"]["schemas"]

    assert "ErrorResponse" in schemas
    assert "GatewayError" in schemas
