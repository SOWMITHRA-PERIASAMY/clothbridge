import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/donation_model.dart';

class DonationService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<String?> addDonation(DonationModel donation) async {
    try {
      await _firestore
          .collection('donations')
          .doc(donation.donationId)
          .set(donation.toMap());

      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Stream<QuerySnapshot> getDonorDonations(String donorId) {
    return _firestore
        .collection('donations')
        .where('donorId', isEqualTo: donorId)
        .orderBy('createdAt', descending: true)
        .snapshots();
  }

  Stream<QuerySnapshot> getPendingDonations() {
    return _firestore
        .collection('donations')
        .where('status', isEqualTo: 'Pending')
        .orderBy('createdAt', descending: true)
        .snapshots();
  }

  Future<void> updateDonationStatus({
    required String donationId,
    required String status,
    String ngoId = "",
  }) async {
    await _firestore.collection('donations').doc(donationId).update({
      'status': status,
      'ngoId': ngoId,
    });
  }
}