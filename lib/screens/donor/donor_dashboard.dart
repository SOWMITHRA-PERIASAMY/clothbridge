import 'package:flutter/material.dart';

import '../../widgets/dashboard/header_card.dart';
import '../../widgets/dashboard/impact_card.dart';
import '../../widgets/dashboard/action_card.dart';
import '../../widgets/dashboard/donation_tile.dart';
import '../../widgets/dashboard/ngo_tile.dart';

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

  @override
  Widget build(BuildContext context) {
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // ================= HEADER =================

              const HeaderCard(
                name: "Sree",
              ),

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
                children: const [

                  ImpactCard(
                    icon: Icons.volunteer_activism,
                    title: "Donations",
                    value: "12",
                    color: Colors.green,
                  ),

                  ImpactCard(
                    icon: Icons.favorite,
                    title: "Lives Helped",
                    value: "48",
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
                          builder: (_) => const DonateClothesScreen(),
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
                          builder: (_) => const DonationHistoryScreen(),
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
                          builder: (_) => const NotificationsScreen(),
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

const DonationTile(
  title: "Winter Jackets",
  ngo: "Hope Foundation",
  status: "Pickup Scheduled",
  date: "Today",
  statusColor: Colors.green,
),

const DonationTile(
  title: "School Uniforms",
  ngo: "Smile Trust",
  status: "Awaiting Pickup",
  date: "Yesterday",
  statusColor: Colors.orange,
),

const SizedBox(height: 30),

const Text(
  "Nearby NGOs",
  style: TextStyle(
    fontSize: 22,
    fontWeight: FontWeight.bold,
  ),
),

const SizedBox(height: 18),

SizedBox(
  height: 180,
  child: ListView(
    scrollDirection: Axis.horizontal,
    children: [

      NgoTile(
        ngoName: "Hope Foundation",
        distance: "2.4 km",
        rating: 4.9,
        onTap: () {},
      ),

      NgoTile(
        ngoName: "Smile Trust",
        distance: "4.8 km",
        rating: 4.8,
        onTap: () {},
      ),

      NgoTile(
        ngoName: "Helping Hands",
        distance: "7.1 km",
        rating: 4.7,
        onTap: () {},
      ),
    ],
  ),
),

const SizedBox(height: 100),
            ],
          ),
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