"""
DonationRepository — abstracted persistence layer.
InMemoryDonationRepository is used in tests/local dev before Firebase is
configured. FirestoreDonationRepository is real, used once credentials exist.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from app.core.config import get_settings
from app.schemas.donation import DonationRecord


class DonationRepository(ABC):
    @abstractmethod
    def save(self, record: DonationRecord) -> None: ...

    @abstractmethod
    def get(self, donation_id: str) -> Optional[DonationRecord]: ...

    @abstractmethod
    def list_by_donor(self, donor_id: str) -> list[DonationRecord]: ...


class InMemoryDonationRepository(DonationRepository):
    def __init__(self) -> None:
        self._store: dict[str, DonationRecord] = {}

    def save(self, record: DonationRecord) -> None:
        self._store[record.donation_id] = record

    def get(self, donation_id: str) -> Optional[DonationRecord]:
        return self._store.get(donation_id)

    def list_by_donor(self, donor_id: str) -> list[DonationRecord]:
        return [r for r in self._store.values() if r.donor_id == donor_id]


class FirestoreDonationRepository(DonationRepository):
    COLLECTION = "donations"

    def __init__(self) -> None:
        from google.cloud import firestore

        settings = get_settings()
        self._client = firestore.Client.from_service_account_json(
            settings.firebase_credentials_path
        )

    def save(self, record: DonationRecord) -> None:
        doc_ref = self._client.collection(self.COLLECTION).document(record.donation_id)
        doc_ref.set(record.model_dump(mode="json"))

    def get(self, donation_id: str) -> Optional[DonationRecord]:
        doc = self._client.collection(self.COLLECTION).document(donation_id).get()
        if not doc.exists:
            return None
        return DonationRecord.model_validate(doc.to_dict())

    def list_by_donor(self, donor_id: str) -> list[DonationRecord]:
        docs = (
            self._client.collection(self.COLLECTION)
            .where("donor_id", "==", donor_id)
            .stream()
        )
        return [DonationRecord.model_validate(d.to_dict()) for d in docs]


_in_memory_singleton = InMemoryDonationRepository()


@lru_cache
def _firestore_singleton() -> FirestoreDonationRepository:
    return FirestoreDonationRepository()


def get_repository() -> DonationRepository:
    settings = get_settings()
    if settings.firebase_credentials_path:
        return _firestore_singleton()
    return _in_memory_singleton
