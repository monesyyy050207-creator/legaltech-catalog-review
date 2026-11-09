from src.legaltech_watch import CatalogEntry, choose_follow_up


def test_signed_delivery_creates_a_deadline_follow_up():
    entry = CatalogEntry("Acme", "https://acme.example", "matter intake", "signed_document", 3)

    decision = choose_follow_up(entry, "catalog snapshot")

    assert decision.observed == "catalog snapshot"
    assert decision.next_action == "send signed document, then follow up in 3 days"
