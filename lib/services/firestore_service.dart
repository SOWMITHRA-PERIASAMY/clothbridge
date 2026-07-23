import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class FirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<Map<String, dynamic>?> getCurrentUserData() async {
    User? user = _auth.currentUser;

    if (user == null) return null;

    DocumentSnapshot doc =
        await _firestore.collection('users').doc(user.uid).get();

    if (doc.exists) {
      return doc.data() as Map<String, dynamic>;
    }

    return null;
  }
}