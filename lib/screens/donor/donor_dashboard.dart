import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../../models/donation_model.dart';
import '../../services/donation_service.dart';
import '../../services/user_service.dart';
import '../../widgets/dashboard/header_card.dart';
import '../../widgets/dashboard/impact_card.dart';
import '../../widgets/dashboard/action_card.dart';
import '../../widgets/dashboard/donation_tile.dart';

import 'donate_clothes_screen.dart';
import 'donation_history_screen.dart';
import 'profile_screen.dart';
import 'notifications_screen.dart';

class DonorDashboard extends StatefulWidget {
  const DonorDashboard({super.key});

  @override
  State<DonorDashboard> createState() => _DonorDashboardState();
}

class _DonorDashboardState extends State<DonorDashboard> {
  int currentIndex = 0;
  final UserService _userService = UserService();
  final DonationService _donationService = DonationService();
  String displayName = "Donor";

  @override
  void initState() {
    super.initState();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final data = await _userService.getUserDetails();
    if (mounted && data != null && data["name"] != null) {
      setState(() {
        displayName = data["name"];
      });
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case "Accepted":
        return Colors.green;
      case "Rejected":
        return Colors.red;
      case "In Upcycling":
        return Colors.orange;
      case "Completed":
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date).inDays;
    if (diff == 0) return "Today";
    if (diff == 1) return "Yesterday";
    return "${date.day}/${date.month}/${date.year}";
  }

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;

    return Scaffold(
      backgroundColor: const Color(0xffF5F7FA),
      appBar: AppBar(
        backgroundColor: const Color(0xffF5F7FA),
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text(
          "ClothBridge",
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color(0xff2E7D32),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(
              Icons.notifications_none,
              color: Colors.black87,
            ),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const NotificationsScreen(),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: user == null
            ? const Center(child: Text("Please log in."))
            : StreamBuilder<QuerySnapshot>(
                stream: _donationService.getDonorDonations(user.uid),
                builder: (context, snapshot) {
                  final docs = snapshot.data?.docs ?? [];
                  final donations = docs
                      .map((d) => DonationModel.fromMap(
                          d.data() as Map<String, dynamic>))
                      .toList();

                  final totalDonations = donations.length;
                  final helpedCount = donations
                      .where((d) =>
                          d.status == "Accepted" ||
                          d.status == "In Upcycling" ||
                          d.status == "Completed")
                      .length;
                  final recentDonations = donations.take(3).toList();

                  return SingleChildScrollView(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        HeaderCard(name: displayName),
                        const SizedBox(height: 28),
                        const Text(
                          "Your Impact",
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 18),
                        Row(
                          children: [
                            ImpactCard(
                              icon: Icons.volunteer_activism,
                              title: "Donations",
                              value: "$totalDonations",
                              color: Colors.green,
                            ),
                            ImpactCard(
                              icon: Icons.favorite,
                              title: "Donations Helped",
                              value: "$helpedCount",
                              color: Colors.red,
                            ),
                          ],
                        ),
                        const SizedBox(height: 30),
                        const Text(
                          "Quick Actions",
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 18),
                        GridView.count(
                          crossAxisCount: 2,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          crossAxisSpacing: 16,
                          mainAxisSpacing: 16,
                          childAspectRatio: 1,
                          children: [
                            ActionCard(
                              icon: Icons.volunteer_activism,
                              title: "Donate",
                              color: Colors.green,
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        const DonateClothesScreen(),
                                  ),
                                );
                              },
                            ),
                            ActionCard(
                              icon: Icons.history,
                              title: "History",
                              color: Colors.orange,
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        const DonationHistoryScreen(),
                                  ),
                                );
                              },
                            ),
                            ActionCard(
                              icon: Icons.notifications,
                              title: "Alerts",
                              color: Colors.blue,
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        const NotificationsScreen(),
                                  ),
                                );
                              },
                            ),
                            ActionCard(
                              icon: Icons.person,
                              title: "Profile",
                              color: Colors.purple,
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const ProfileScreen(),
                                  ),
                                );
                              },
                            ),
                          ],
                        ),
                        const SizedBox(height: 30),
                        const Text(
                          "Recent Donations",
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 18),
                        if (recentDonations.isEmpty)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 20),
                            child: Text(
                              "No donations yet — tap Donate to get started.",
                              style: TextStyle(color: Colors.grey.shade600),
                            ),
                          )
                        else
                          ...recentDonations.map(
                            (donation) => DonationTile(
                              title: donation.category,
                              ngo: donation.status == "Pending"
                                  ? "Awaiting NGO review"
                                  : "NGO assigned",
                              status: donation.status,
                              date: _formatDate(donation.createdAt),
                              statusColor: _statusColor(donation.status),
                            ),
                          ),
                        const SizedBox(height: 100),
                      ],
                    ),
                  );
                },
              ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xff2E7D32),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text("Donate"),
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const DonateClothesScreen(),
            ),
          );
        },
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIndex,
        selectedItemColor: const Color(0xff2E7D32),
        unselectedItemColor: Colors.grey,
        type: BottomNavigationBarType.fixed,
        onTap: (index) {
          setState(() {
            currentIndex = index;
          });

          switch (index) {
            case 0:
              break;
            case 1:
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const DonationHistoryScreen(),
                ),
              );
              break;
            case 2:
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const NotificationsScreen(),
                ),
              );
              break;
            case 3:
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const ProfileScreen(),
                ),
              );
              break;
          }
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: "Home",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: "History",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.notifications),
            label: "Alerts",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: "Profile",
          ),
        ],
      ),
    );
  }
}
