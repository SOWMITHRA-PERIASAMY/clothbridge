import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../../models/donation_model.dart';
import '../../services/donation_service.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  (IconData, Color, String) _presentation(String status) {
    switch (status) {
      case "Accepted":
        return (Icons.check_circle, Colors.green, "was accepted by an NGO");
      case "Rejected":
        return (Icons.cancel, Colors.red, "was not accepted this time");
      case "In Upcycling":
        return (Icons.autorenew, Colors.orange, "is being upcycled");
      case "Completed":
        return (Icons.emoji_events, Colors.blue, "upcycling was completed");
      default:
        return (Icons.hourglass_top, Colors.grey, "is pending review");
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;
    final donationService = DonationService();

    return Scaffold(
      backgroundColor: const Color(0xffF5F7FA),
      appBar: AppBar(
        title: const Text("Notifications"),
        backgroundColor: const Color(0xff2E7D32),
        foregroundColor: Colors.white,
      ),
      body: user == null
          ? const Center(child: Text("Please log in."))
          : StreamBuilder<QuerySnapshot>(
              stream: donationService.getDonorDonations(user.uid),
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
                    child: Text(
                      "No notifications yet.\nUpdates on your donations will show up here.",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 16, color: Colors.grey),
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
                    final (icon, color, message) =
                        _presentation(donation.status);

                    return Card(
                      elevation: 1,
                      margin: const EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: color.withOpacity(0.15),
                          child: Icon(icon, color: color),
                        ),
                        title: Text(
                          "Your ${donation.category} donation $message",
                        ),
                        subtitle: Text(
                          "${donation.createdAt.day}/${donation.createdAt.month}/${donation.createdAt.year}",
                          style: const TextStyle(fontSize: 12),
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
