import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../../models/donation_model.dart';
import '../../services/donation_service.dart';

class NgoDashboard extends StatefulWidget {
  const NgoDashboard({super.key});

  @override
  State<NgoDashboard> createState() => _NgoDashboardState();
}

class _NgoDashboardState extends State<NgoDashboard> {
  final DonationService _donationService = DonationService();
  final Set<String> _processingIds = {};

  Future<void> _respond(String donationId, String status) async {
    setState(() => _processingIds.add(donationId));
    try {
      final ngoId = FirebaseAuth.instance.currentUser?.uid ?? "";
      await _donationService.updateDonationStatus(
        donationId: donationId,
        status: status,
        ngoId: status == "Accepted" ? ngoId : "",
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Donation $status")),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to update: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _processingIds.remove(donationId));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xffF5F7FA),
      appBar: AppBar(
        title: const Text("NGO Dashboard"),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: StreamBuilder<QuerySnapshot>(
        stream: _donationService.getPendingDonations(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          }
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final docs = snapshot.data?.docs ?? [];

          return Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                color: Colors.blue,
                child: Text(
                  "${docs.length} pending donation${docs.length == 1 ? '' : 's'} to review",
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Expanded(
                child: docs.isEmpty
                    ? const Center(
                        child: Text(
                          "No pending donations right now.",
                          style: TextStyle(fontSize: 16, color: Colors.grey),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: docs.length,
                        itemBuilder: (context, index) {
                          final data =
                              docs[index].data() as Map<String, dynamic>;
                          final donation = DonationModel.fromMap(data);
                          final isProcessing =
                              _processingIds.contains(donation.donationId);

                          return Card(
                            elevation: 2,
                            margin: const EdgeInsets.only(bottom: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      ClipRRect(
                                        borderRadius:
                                            BorderRadius.circular(12),
                                        child: donation.imageUrls.isNotEmpty
                                            ? Image.network(
                                                donation.imageUrls.first,
                                                width: 70,
                                                height: 70,
                                                fit: BoxFit.cover,
                                                errorBuilder:
                                                    (_, __, ___) => Container(
                                                  width: 70,
                                                  height: 70,
                                                  color: Colors.grey.shade200,
                                                  child: const Icon(Icons
                                                      .image_not_supported),
                                                ),
                                              )
                                            : Container(
                                                width: 70,
                                                height: 70,
                                                color: Colors.grey.shade200,
                                                child: const Icon(
                                                    Icons.checkroom),
                                              ),
                                      ),
                                      const SizedBox(width: 14),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              "${donation.category} · ${donation.size}",
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              "Condition: ${donation.condition}",
                                              style: const TextStyle(
                                                  fontSize: 13,
                                                  color: Colors.grey),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              "By: ${donation.donorName}",
                                              style: const TextStyle(
                                                  fontSize: 13,
                                                  color: Colors.grey),
                                            ),
                                            if (donation
                                                .description.isNotEmpty) ...[
                                              const SizedBox(height: 6),
                                              Text(
                                                donation.description,
                                                maxLines: 2,
                                                overflow:
                                                    TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                    fontSize: 13),
                                              ),
                                            ],
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 14),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: OutlinedButton.icon(
                                          onPressed: isProcessing
                                              ? null
                                              : () => _respond(
                                                  donation.donationId,
                                                  "Rejected"),
                                          icon: const Icon(Icons.close,
                                              color: Colors.red),
                                          label: const Text("Reject",
                                              style: TextStyle(
                                                  color: Colors.red)),
                                          style: OutlinedButton.styleFrom(
                                            side: const BorderSide(
                                                color: Colors.red),
                                            shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(12),
                                            ),
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: ElevatedButton.icon(
                                          onPressed: isProcessing
                                              ? null
                                              : () => _respond(
                                                  donation.donationId,
                                                  "Accepted"),
                                          icon: isProcessing
                                              ? const SizedBox(
                                                  width: 16,
                                                  height: 16,
                                                  child:
                                                      CircularProgressIndicator(
                                                    strokeWidth: 2,
                                                    color: Colors.white,
                                                  ),
                                                )
                                              : const Icon(Icons.check),
                                          label: const Text("Accept"),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.blue,
                                            foregroundColor: Colors.white,
                                            shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(12),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
