import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

import '../../models/donation_model.dart';
import '../../services/donation_service.dart';

/// Basic SHG (Self Help Group) dashboard.
///
/// Scope note: this is intentionally a basic first version. It shows
/// donations that NGOs have accepted ("Accepted" = available to start
/// upcycling) and lets an SHG move them through "In Upcycling" ->
/// "Completed". There is no dedicated SHG assignment/claiming system yet
/// (any SHG user can act on any accepted donation) — that's a reasonable
/// next-iteration improvement, not built here.
class ShgDashboard extends StatefulWidget {
  const ShgDashboard({super.key});

  @override
  State<ShgDashboard> createState() => _ShgDashboardState();
}

class _ShgDashboardState extends State<ShgDashboard> {
  final DonationService _donationService = DonationService();
  final Set<String> _processingIds = {};

  Future<void> _updateStatus(String donationId, String status) async {
    setState(() => _processingIds.add(donationId));
    try {
      await _donationService.updateDonationStatus(
        donationId: donationId,
        status: status,
      );
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

  Stream<QuerySnapshot> _relevantDonations() {
    return FirebaseFirestore.instance
        .collection('donations')
        .where('status', whereIn: ['Accepted', 'In Upcycling'])
        .orderBy('createdAt', descending: true)
        .snapshots();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xffF5F7FA),
      appBar: AppBar(
        title: const Text("SHG Dashboard"),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
      ),
      body: StreamBuilder<QuerySnapshot>(
        stream: _relevantDonations(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          }
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final docs = snapshot.data?.docs ?? [];
          if (docs.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  "No items available for upcycling right now.",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.grey),
                ),
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: docs.length,
            itemBuilder: (context, index) {
              final donation = DonationModel.fromMap(
                docs[index].data() as Map<String, dynamic>,
              );
              final isProcessing =
                  _processingIds.contains(donation.donationId);
              final inProgress = donation.status == "In Upcycling";

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
                        children: [
                          Expanded(
                            child: Text(
                              "${donation.category} · ${donation.size}",
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: (inProgress ? Colors.orange : Colors.green)
                                  .withOpacity(0.12),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              donation.status,
                              style: TextStyle(
                                color:
                                    inProgress ? Colors.orange : Colors.green,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        "Condition: ${donation.condition}",
                        style:
                            const TextStyle(fontSize: 13, color: Colors.grey),
                      ),
                      const SizedBox(height: 14),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: isProcessing
                              ? null
                              : () => _updateStatus(
                                  donation.donationId,
                                  inProgress ? "Completed" : "In Upcycling"),
                          icon: isProcessing
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Icon(inProgress
                                  ? Icons.emoji_events
                                  : Icons.autorenew),
                          label: Text(
                              inProgress ? "Mark Completed" : "Start Upcycling"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.teal,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
