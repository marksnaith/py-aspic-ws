import pymongo
import random
from argtech import ws
from pyaspic import *

_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

@ws.group
class Theory:
    """
    Create and evaluate Argumentation Theories
    """

    def __init__(self):
        mongo = pymongo.MongoClient("mongodb://aspic-ws-mongo:27017/")
        db = mongo["aspic"]
        self.arguments_db = db["arguments"]

        self.blank_theory = {
            "axioms": [],
            "premises": [],
            "assumptions": [],
            "kbPrefs": [],
            "rules": {},
            "rulePrefs": [],
            "contrariness": []
        }

    @ws.method("/evaluate", methods=["POST"])
    def evaluate(self):
        """
        @/app/docs/theory/evaluate.yml
        """

        warnings = []

        available_semantics = ["grounded", "preferred"]

        # tidy up the query string parameters
        args = {k: v.lower().strip() for k,v in ws.request.args.items() if v.strip() != ""}

        data = ws.request.get_json(force=True)

        semantics = data.get("semantics","grounded")
        if semantics not in available_semantics:
            warnings.append("Semantics '{}' not recognised; using grounded instead".format(str(semantics)))
            semantics = "grounded"

        ordering = data.get("ordering", "weakest")
        if ordering != "weakest" and ordering != "last":
            warnings.append("Ordering '{}' not recognised; using weakest instead".format(str(ordering)))
            ordering = "weakest"

        query = data.get("query",None)
        save = (args.get("save","false") == "true")
        transposition = (args.get("transposition","false") == "true")

        theory = data.get("theory", None)

        if theory is not None:
            system = ArgumentationSystem(transposition)
            kb = KnowledgeBase()

            # build the knowledge base
            for a in theory.get("axioms",[]):
                kb.add_axiom(Formula(a))

            for p in theory.get("premises", []):
                kb.add_premise(Formula(p))

            for a in theory.get("assumptions",[]):
                kb.add_assumption(Formula(a))

            # knowledge base preferences
            for pref in theory.get("kbPrefs",[]):
                p = pref.split("<")
                kb.add_preference((p[0], p[1]))

            # add the rules
            for label, rule in theory.get("rules",{}).items():
                rule = Rule.from_string(label, rule)
                system.add_rule(rule)

            # rule preferences
            for pref in theory.get("rulePrefs",[]):
                p = pref.split("<")
                system.add_rule_preference((p[0], p[1]))

            # contrariness
            for c in theory.get("contrariness",[]):
                contradiction = False
                symbol = "-"

                if "^" in c:
                    symbol = "^"
                elif "-" in c:
                    symbol = "-"
                    contradiction = True
                else:
                    continue

                c = c.split(symbol)
                system.add_contrary((c[0],c[1]), contradiction)

        at = ArgumentationTheory(system, kb, ordering=ordering, engine="http://aspic-ws-dung-o-matic")

        well_formed, reason = at.check_well_formed()
        result, query_response = at.evaluate(semantics=semantics, query=query)

        response = {
            "wellFormed": well_formed,
            "wellFormedReason": reason,
            "queryResponse": query_response,
            "warnings": warnings,
            "result": result
        }

        if save:
            response["id"] = self.save(theory, semantics, ordering, query, transposition)

        return response, 200

    @ws.method("/<id>", methods=["GET"])
    def load(self, id):
        """
        @/app/docs/theory/load.yml
        """

        result = self.arguments_db.find_one({"id": id}, {"_id": False})

        if result:
            return result, 200
        else:
            return "Theory not found", 404


    def save(self, theory, semantics, ordering, query, transposition):
        """
        Saves the given theory
        """

        #populate missing fields in the theory
        for k,v in self.blank_theory.items():
            if k not in theory:
                theory[k] = v

        id = self.generate_id()

        doc = {
            "id": id,
            "semantics": semantics,
            "ordering": ordering,
            "query": query,
            "transposition": transposition,
            "theory": theory
        }

        self.arguments_db.insert_one(doc)

        return id

    def generate_id(self):
        id = str(random.randint(0,9))
        max = len(_alphabet) - 1

        for i in range(0,5):
            id = id + _alphabet[random.randint(0,max)]

        result = self.arguments_db.find_one({"id": id})

        if result:
            return self.generate_id()
        else:
            return id
