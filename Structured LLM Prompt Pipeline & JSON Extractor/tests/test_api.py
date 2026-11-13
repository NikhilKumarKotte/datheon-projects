import io


def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert "invoice" in data["supported_schemas"]
    assert "resume" in data["supported_schemas"]
    assert "receipt" in data["supported_schemas"]


def test_schemas_endpoint(test_client):
    response = test_client.get("/api/v1/schemas")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_extract_text_endpoint(test_client):
    payload = {
        "text": "Invoice INV-1042 Acme Corp Total 100",
        "document_type": "invoice",
    }
    response = test_client.post("/api/v1/extract", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    assert res_data["data"]["invoice_number"] == "TEST-123"
    assert res_data["metadata"]["document_type"] == "invoice"


def test_extract_empty_text_endpoint(test_client):
    payload = {
        "text": "   ",
        "document_type": "invoice",
    }
    response = test_client.post("/api/v1/extract", json=payload)
    assert response.status_code == 400


def test_extract_file_upload_endpoint(test_client):
    file_content = b"Invoice INV-1042 Acme Corp Total 100"
    files = {
        "file": ("invoice.txt", io.BytesIO(file_content), "text/plain"),
    }
    data = {"document_type": "invoice"}
    response = test_client.post("/api/v1/extract/upload", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["invoice_number"] == "TEST-123"
