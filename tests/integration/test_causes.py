import datetime
import json
from http import HTTPStatus
from unittest.mock import patch
from datetime import datetime

from app import app
import pytest

from app.auth.models.user_model import UserModel
from app.auth.utils import encode_jwt_token
from app.cause_problem_association.models import CauseAndProblemAssociation

from app.causes.models import CustomCauseModel, DefaultCauseModel, CauseIndicatorModel, CauseIndicatorDataModel
from app.problems.models import ProblemModel
from db import db


@pytest.fixture
def test_app():
    # no se ha camiado la BD por SQLite por que SQLite no admite columnas de tipo ARRAY. y exiten unas al momento de migrar
    # Esta url viene del docker-compose-local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mysecretpassword@192.168.1.5:5432/safecities_flask'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


@pytest.fixture
def client(test_app):
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_db_connection(client):
    with app.app_context():
        db.engine.dispose()
        try:
            db.engine.connect()
            assert True
        except Exception as e:
            assert False, f"Error al conectar a la base de datos: {e}"


def test_list_causes_controller(client):
    query_params = {
        "page": 1,
        "page_size": 10,
        "order_field": "name",
        "sort_type": "asc",
        "fields": ["id", "name", "type"]
    }

    response = client.get("/causes", query_string=query_params)

    assert response.status_code == HTTPStatus.OK

    data = json.loads(response.data.decode("utf-8"))
    assert "code" in data
    assert "data" in data

    assert data["code"] == HTTPStatus.OK

    assert "total_items" in data["data"]
    assert "total_pages" in data["data"]
    assert "results" in data["data"]

    expected_response = {'results': [], 'total_items': 0, 'total_pages': 0}

    assert expected_response == data["data"]


def test_summary_controller(client):
    response = client.get("/causes/summary")

    assert response.status_code == HTTPStatus.OK

    data = json.loads(response.data.decode("utf-8"))

    assert "code" in data
    assert "data" in data

    assert data["code"] == HTTPStatus.OK
    assert "totalCauses" in data["data"]
    assert "totalPrioritizedCauses" in data["data"]
    assert "totalRelevantCauses" in data["data"]

    expected_response = {'totalCauses': 0, 'totalPrioritizedCauses': 0, 'totalRelevantCauses': 0}

    assert expected_response == data["data"]


def test_get_default_cause_controller(client):
    default_cause = DefaultCauseModel(
        id=1,
        name="Cause Name",
        justification="Cause Justification"
    )

    with patch("app.causes.services.get_default_cause") as mock_get_default_cause:
        mock_get_default_cause.return_value = default_cause

        response = client.get('/causes/default-causes/1')

        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data.decode("utf-8"))
        assert "code" in data
        assert "data" in data
        assert data["code"] == HTTPStatus.OK
        assert "id" in data["data"]
        assert "name" in data["data"]
        assert "justification" in data["data"]

        expected_response = {'id': 1, 'justification': 'Cause Justification', 'name': 'Cause Name', 'prioritized': True}

        assert expected_response == data["data"]


def test_get_default_cause_controller_not_found(client):
    with patch("app.causes.services.get_default_cause") as mock_get_default_cause:
        mock_get_default_cause.return_value = None

        response = client.get('/causes/default-causes/9')

        assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_cause_indicators_controller(client):
    cause_indicators_with_data = [
        (CauseIndicatorModel(id=1,
                             name="Ind1",
                             cause_id=1),
         CauseIndicatorDataModel(cause_indicator_id=1,
                                 period="2023-09-01")),
        (CauseIndicatorModel(id=2,
                             name="Ind2",
                             cause_id=1),
         CauseIndicatorDataModel(cause_indicator_id=2,
                                 period="2023-09-01")),
    ]

    with patch("app.causes.services.list_cause_indicators_with_last_data") as mock_list_cause_indicators_with_last_data:
        mock_list_cause_indicators_with_last_data.return_value = cause_indicators_with_data

        response = client.get('/causes/1/indicators/all')

        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data.decode("utf-8"))
        assert "code" in data
        assert "data" in data
        assert data["code"] == HTTPStatus.OK
        assert "causeIndicatorData" in data["data"][0]
        assert "causeIndicatorData" in data["data"][1]
        assert "causeIndicator" in data["data"][0]
        assert "causeIndicator" in data["data"][1]
        assert "id" in data["data"][0]["causeIndicator"]
        assert "id" in data["data"][1]["causeIndicator"]
        assert "name" in data["data"][0]["causeIndicator"]
        assert "name" in data["data"][1]["causeIndicator"]
        assert "cause_id" in data["data"][0]["causeIndicator"]
        assert "cause_id" in data["data"][1]["causeIndicator"]
        assert "period" in data["data"][0]["causeIndicatorData"]
        assert "period" in data["data"][1]["causeIndicatorData"]

        expected_response = {'id': 1, 'justification': 'Cause Justification', 'name': 'Cause Name', 'prioritized': True}


def test_list_cause_indicators_controller_empty(client):
    with patch("app.causes.services.list_cause_indicators_with_last_data") as mock_list_cause_indicators_with_last_data:
        mock_list_cause_indicators_with_last_data.return_value = []

        response = client.get('/causes/1/indicators/all')

        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data.decode("utf-8"))
        assert "code" in data
        assert "data" in data
        assert data["code"] == HTTPStatus.OK
        assert len(data["data"]) == 0


def test_get_custom_cause_controller(client):
    user = UserModel(
        id=1,
        name="Name",
        last_name="LastName",
        email='u@email.com'
    )

    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()

    custom_cause = CustomCauseModel(
        id=1,
        name="Name",
        justification="Justification",
        evidences="Evidences",
        created_by=user,
        created_at=created_at,
        updated_at=updated_at
    )

    db.session.add(custom_cause)
    db.session.commit()

    assert custom_cause.id is not None

    with patch("app.causes.services.get_custom_cause") as mock_get_custom_cause:
        mock_get_custom_cause.return_value = custom_cause

        response = client.get('/causes/custom-causes/1')

        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data.decode("utf-8"))

        createdAt = data['data']['createdAt']
        updatedAt = data['data']['updatedAt']

        expected_response = {
            'annexes': [],
            'createdAt': createdAt,
            'createdBy': {'id': 1, 'lastName': 'LastName', 'name': 'Name'},
            'evidences': 'Evidences',
            'id': 1,
            'justification': 'Justification',
            'name': 'Name',
            'problems': [],
            'references': None,
            'type': 'custom_cause',
            'updatedAt': updatedAt
        }

        assert data['data'] == expected_response



def test_list_cause_related_problem_controller(client):
    user = UserModel(
        id=1,
        name="Name",
        last_name="LastName",
        email='u@email.com'
    )

    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()

    custom_cause = CustomCauseModel(
        id=1,
        name="Name",
        justification="Justification",
        evidences="Evidences",
        created_by=user,
        created_at=created_at,
        updated_at=updated_at
    )

    db.session.add(custom_cause)
    db.session.commit()

    assert custom_cause.id is not None

    problem1 = ProblemModel(
        id="PE001",
        name="Problem1",
        description="Description1",
    )
    problem2 = ProblemModel(
        id="PE002",
        name="Problem2",
        description="Description2",
    )
    db.session.add(problem1)
    db.session.add(problem2)
    db.session.commit()

    assert problem1.id is not None
    assert problem2.id is not None

    association1 = CauseAndProblemAssociation(
        cause_id=custom_cause.id,
        problem_id=problem1.id,
        prioritized=True
    )
    association2 = CauseAndProblemAssociation(
        cause_id=custom_cause.id,
        problem_id=problem2.id,
        prioritized=False
    )
    db.session.add(association1)
    db.session.add(association2)
    db.session.commit()

    assert association1.id is not None
    assert association2.id is not None

    response = client.get(f'/causes/{custom_cause.id}/problems/all')

    assert response.status_code == HTTPStatus.OK

    data = json.loads(response.data.decode("utf-8"))

    expected_response = [{'prioritized': True, 'problemId': 'PE001', 'problemName': 'Problem1'},
                         {'prioritized': False, 'problemId': 'PE002', 'problemName': 'Problem2'}]

    assert "data" in data
    assert expected_response == data["data"]


# not working
def test_post_custom_causes(client):

    data = [{
        "name": "Nombre",
        "justification": "Justificación",
        "evidences": "Evidencia"
    }]

    response = client.post("/causes/custom-causes", json=data)

    assert response.status_code == HTTPStatus.OK
