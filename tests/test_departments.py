def test_create_department(client):
    response = client.post("/departments/", json={"name": "Engineering"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering"
    assert data["parent_id"] is None
    assert "id" in data


def test_create_department_trims_name(client):
    response = client.post("/departments/", json={"name": "  Backend  "})
    assert response.status_code == 201
    assert response.json()["name"] == "Backend"


def test_duplicate_name_under_same_parent_conflict(client):
    client.post("/departments/", json={"name": "Backend"})
    response = client.post("/departments/", json={"name": "Backend"})
    assert response.status_code == 409


def test_create_employee_in_department(client):
    department = client.post("/departments/", json={"name": "HR"}).json()
    response = client.post(
        f"/departments/{department['id']}/employees/",
        json={"full_name": "Jane Doe", "position": "Recruiter"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Jane Doe"
    assert data["department_id"] == department["id"]


def test_create_employee_unknown_department_404(client):
    response = client.post(
        "/departments/999/employees/",
        json={"full_name": "John", "position": "Dev"},
    )
    assert response.status_code == 404


def test_get_department_tree_with_depth(client):
    root = client.post("/departments/", json={"name": "Root"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Child", "parent_id": root["id"]},
    ).json()
    client.post(
        f"/departments/{root['id']}/employees/",
        json={"full_name": "Alice", "position": "Lead"},
    )

    response = client.get(f"/departments/{root['id']}?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert data["department"]["name"] == "Root"
    assert len(data["employees"]) == 1
    assert len(data["children"]) == 1
    assert data["children"][0]["department"]["name"] == "Child"


def test_move_department_cycle_conflict(client):
    root = client.post("/departments/", json={"name": "Root"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Child", "parent_id": root["id"]},
    ).json()

    response = client.patch(
        f"/departments/{root['id']}",
        json={"parent_id": child["id"]},
    )
    assert response.status_code == 409


def test_delete_department_cascade(client):
    root = client.post("/departments/", json={"name": "Root"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Child", "parent_id": root["id"]},
    ).json()
    client.post(
        f"/departments/{child['id']}/employees/",
        json={"full_name": "Bob", "position": "Dev"},
    )

    response = client.delete(f"/departments/{root['id']}?mode=cascade")
    assert response.status_code == 204
    assert client.get(f"/departments/{root['id']}").status_code == 404
    assert client.get(f"/departments/{child['id']}").status_code == 404


def test_delete_department_reassign(client):
    source = client.post("/departments/", json={"name": "Source"}).json()
    target = client.post("/departments/", json={"name": "Target"}).json()
    client.post(
        f"/departments/{source['id']}/employees/",
        json={"full_name": "Carl", "position": "Analyst"},
    )

    response = client.delete(
        f"/departments/{source['id']}?mode=reassign&reassign_to_department_id={target['id']}",
    )
    assert response.status_code == 204

    tree = client.get(f"/departments/{target['id']}").json()
    assert len(tree["employees"]) == 1
    assert tree["employees"][0]["full_name"] == "Carl"
