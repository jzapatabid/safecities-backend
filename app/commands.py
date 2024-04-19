import csv
from typing import List, Optional

import click
from sqlalchemy import select, delete

from app import app
from app.auth.models.user_model import UserModel
from app.auth.schemas.create_user_schema import SignUpSchema
from app.auth.services import hash_password
from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import DefaultCauseModel, CauseIndicatorModel
from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.commons.models.neighborhood_model import NeighborhoodModel
from app.initiatives.models import InitiativeModel, InitiativeCauseProblemAssociationModel, InitiativeOutcomeModel, \
    InitiativeOutcomeAssociationModel
from app.plan.models import MacroObjectiveModel, MacroObjectiveProblemAssociationModel, FocusModel, \
    FocusAssociationModel
from app.problems.models import ProblemModel
from db import db

cost_level_dict = dict(
    low=1,
    medium=2,
    high=3,
)

efficiency_level_dict = dict(
    negative_effect=1,
    no_effect=2,
    mixed_evidence=3,
    promising=4,
    effective=5,
)


@app.cli.command("load_products")
def load_products():
    with open("data/new/products.csv", "r", encoding="utf-8-sig") as csv_file:
        data = csv.DictReader(csv_file)
        for item in data:
            model = InitiativeOutcomeModel(
                id=item["id"],
                name=item["name"],
            )
            db.session.merge(model)
    db.session.commit()


@app.cli.command("load_neighborhoods")
def load_neighborhoods():
    with open("data/new/neighborhoods.csv", "r", encoding="utf-8-sig") as csv_file:
        data = csv.DictReader(csv_file)
        for item in data:
            model = NeighborhoodModel(
                id=item["id"],
                name=item["name"],
            )
            db.session.merge(model)
    db.session.commit()


@app.cli.command("load_muni")
def load_muni():
    with open("data/new/muni_departments.csv", "r", encoding="utf-8-sig") as csv_file:
        data = csv.DictReader(csv_file)
        for item in data:
            insert_data = MunicipalDepartmentModel(
                id=item["id"],
                name=item["name"].strip().lower(),
            )
            db.session.merge(insert_data)
        db.session.commit()


@app.cli.command("load_problems")
def load_problems():
    with open("data/new/problem.csv", "r", encoding='utf-8-sig') as csv_file:
        data = csv.DictReader(csv_file)
        for item in data:
            problem_model = db.session.execute(
                select(ProblemModel)
                .where(ProblemModel.code == item["code"].lower())
            ).scalar()
            if not problem_model:
                problem_model = ProblemModel()

            problem_model.code = item["code"].lower()
            problem_model.name = item["name"].lower()
            problem_model.description = item["description"].lower()
            problem_model.indicator_name = item["indicator_name"].lower()
            problem_model.measurement_unit = item["measurement_unit"].lower()
            problem_model.indicator_code = item["indicator_code"].lower()
            problem_model.polarity = item["polarity"].lower()
            problem_model.is_default = True

            db.session.merge(problem_model)
        db.session.commit()


@app.cli.command("load_causes")
def load_causes():
    with open("data/new/causes.csv", "r", encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for item in csv_reader:

            cause_model: Optional[DefaultCauseModel] = db.session.execute(
                select(DefaultCauseModel)
                .where(DefaultCauseModel.code == item["code"].strip().lower())
            ).scalar()

            if not cause_model:
                cause_model = DefaultCauseModel()

            cause_model.code = item["code"].strip().lower()
            cause_model.name = item["name"].strip().lower()
            cause_model.justification = item["description"].strip()
            if cause_model.id:
                db.session.merge(cause_model)
            else:
                db.session.add(cause_model)
            db.session.commit()

            # relate problem and causes
            problem_codes: List[str] = item["problem"].lower().strip().split(",")
            
            for problem_code in problem_codes:
                problem_model = db.session.execute(
                    select(ProblemModel)
                    .where(ProblemModel.code == problem_code)
                ).scalar()

                if problem_model:
                    cause_problem_association_model = CauseAndProblemAssociation(
                        cause_id=cause_model.id,
                        problem_id=problem_model.id
                    )
                    db.session.add(cause_problem_association_model)
                    db.session.commit()


@app.cli.command("load_cause_indicators")
def load_cause_indicators():
    with open("data/new/cause_indicators.csv", "r", encoding='utf-8-sig') as csv_file:
        data = csv.DictReader(csv_file)
        for item in data:

            cause_codes = item["cause"].strip().lower().split(",")  # this is a patch

            for i, cause_code in enumerate(cause_codes):

                cause_indicator_model = db.session.execute(
                    select(CauseIndicatorModel)
                    .join(
                        DefaultCauseModel,
                        DefaultCauseModel.id == CauseIndicatorModel.cause_id)
                    .where(CauseIndicatorModel.code == item["code"].strip().lower(),
                           DefaultCauseModel.code == cause_code
                           )
                ).scalar()

                if cause_indicator_model:
                    continue
                else:
                    cause_indicator_model = CauseIndicatorModel()

                print(cause_code)
                print("*-*-*-**-*-*-*-**-*-*-**-*-*-*-**-*-*-**-*-*-*-**-*-*-**-*-*-*-*")
                cause_model: DefaultCauseModel = db.session.execute(
                    select(DefaultCauseModel)
                    .where(DefaultCauseModel.code == cause_code)
                ).scalar()

                if not cause_model:
                    # this is anpther patch in case cause_code doesnt exist in database
                    continue

                cause_indicator_model.cause_id = cause_model.id
                cause_indicator_model.code = item["code"].strip().lower()
                cause_indicator_model.name = item["name"].strip().lower()
                cause_indicator_model.measurement_unit = item["measurement_unit"].strip().lower()
                cause_indicator_model.polarity = item["polarity"].strip().lower()
                db.session.add(cause_indicator_model)
        db.session.commit()


@app.cli.command("load_initiatives")
def load_initiatives():
    with open("data/new/initiatives.csv", 'r', newline='', encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for c, item in enumerate(csv_reader):
            code = item["code"].strip().lower()
            name = item["name"].strip().lower()
            justification = item["justification"].strip()
            evidences = item["evidences"].strip()
            cost_level = cost_level_dict.get(item["cost_level"].strip())
            efficiency_level = efficiency_level_dict.get(item["efficiency_level"].strip())
            cause_problem_codes: List[str] = list(set([
                cause_problem_code.strip()
                for cause_problem_code in item["cause_problem_codes"].strip().lower().split(",")
            ]))
            reference_urls: List[str] = [
                url.strip()
                for url in item["reference_urls"].strip().split(",")
            ]
            department_ids: List[int] = [
                int(department_id.strip())
                for department_id in item["department_ids"].strip().split(",")
            ]
            product_ids: List[int] = list(set([
                int(department_id.strip())
                for department_id in item["product_ids"].strip().split(",")
            ]))

            initiative_model = db.session.execute(
                select(InitiativeModel)
                .where(InitiativeModel.code == code)
            ).scalar()
            if not initiative_model:
                initiative_model = InitiativeModel()

            initiative_model.code = code
            initiative_model.name = name
            initiative_model.justification = justification
            initiative_model.evidences = evidences
            initiative_model.cost_level = cost_level
            initiative_model.efficiency_level = efficiency_level
            initiative_model.is_default = True
            initiative_model.reference_urls = reference_urls

            if initiative_model.id is None:
                db.session.add(initiative_model)
            # db.session.commit()

            department_models = list()
            for department_id in department_ids:
                deparment_model = db.session.execute(
                    select(MunicipalDepartmentModel)
                    .where(MunicipalDepartmentModel.id == department_id)
                    .limit(1)
                ).scalar_one()
                department_models.append(deparment_model)
            initiative_model.municipal_departments.extend(department_models)

            # db.session.execute(
            #     delete(InitiativeOutcomeAssociationModel)
            #     .where(InitiativeOutcomeAssociationModel.initiative_outcome_id == initiative_model.id)
            # )
            for product_id in product_ids:
                db.session.add(
                    InitiativeOutcomeAssociationModel(
                        initiative_id=initiative_model.id,
                        initiative_outcome_id=product_id
                    )
                )

            for cause_problem_code in cause_problem_codes:
                if not cause_problem_code:
                    continue
                try:
                    cause_code, problem_code = cause_problem_code.split("-")
                except:
                    print(cause_problem_code)
                    print("*-*-*-*-*")
                    raise
                cause_query = select(DefaultCauseModel).where(DefaultCauseModel.code == cause_code.lower())
                cause_model = db.session.execute(cause_query).scalar()
                problem_model = db.session.execute(
                    select(ProblemModel)
                    .where(ProblemModel.code == problem_code.lower())
                ).scalar()
                if not problem_model:
                    # todo fixit
                    continue
                association_model = InitiativeCauseProblemAssociationModel(
                    initiative_id=initiative_model.id,
                    cause_id=cause_model.id,
                    problem_id=problem_model.id,
                )
                db.session.add(association_model)
                db.session.commit()


@app.cli.command("load_macro")
def load_macro():
    with open("data/new/macro_obj.csv", 'r', newline='', encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for item in csv_reader:
            macro_model = MacroObjectiveModel(
                id=item["id"].lower().strip(),
                name=item["name"].lower().strip(),
            )
            db.session.merge(macro_model)

            if not item["problem_code"]:
                continue

            for problem_code in item["problem_code"].lower().strip().split(","):
                problem_model = db.session.execute(
                    select(ProblemModel).where(ProblemModel.code == problem_code)
                ).scalar()
                association_model = MacroObjectiveProblemAssociationModel(
                    macro_objective_id=macro_model.id,
                    problem_id=problem_model.id,
                )
                db.session.merge(association_model)
        db.session.commit()


@app.cli.command("load_focuses")
def load_focuses():
    with open("data/new/focus.csv", 'r', newline='', encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for c, item in enumerate(csv_reader):
            focus_model = FocusModel(
                id=item["id"].lower().strip(),
                name=item["name"].lower().strip(),
            )
            db.session.merge(focus_model)
            db.session.commit()

            if not item["macroobj_causeind_codes"]:
                continue

            macroobj_causeind_codes = item["macroobj_causeind_codes"].lower().strip().split(",")

            for macroobj_causeind_code in macroobj_causeind_codes:
                macroobj_id, causeind_code = macroobj_causeind_code.split("-")

                causeind_id = db.session.execute(
                    select(CauseIndicatorModel.id)
                    .where(CauseIndicatorModel.code == causeind_code)
                ).scalar()

                if not causeind_id:
                    # this is another patch
                    continue

                association_model = FocusAssociationModel(
                    focus_id=focus_model.id,
                    macro_objective_id=macroobj_id,
                    cause_indicator_id=causeind_id,
                )
                db.session.merge(association_model)
        db.session.commit()


@app.cli.command("create_admin_user")
def create_admin_user():
    email = input("email: ")
    password = input("password: ")
    name = input("name: ")
    last_name = input("last_name: ")

    user_model = UserModel(
        email=email,
        password=hash_password(password),
        name=name,
        last_name=last_name,
        is_active=True,
        is_admin=True,
    )
    db.session.add(user_model)
    db.session.commit()


@app.cli.command("load_data")
@click.pass_context
def load_data(ctx):
    ctx.invoke(load_products)
    ctx.invoke(load_neighborhoods)
    ctx.invoke(load_muni)
    ctx.invoke(load_problems)
    ctx.invoke(load_causes)
    ctx.invoke(load_cause_indicators)
    ctx.invoke(load_initiatives)
    ctx.invoke(load_macro)
    ctx.invoke(load_focuses)
