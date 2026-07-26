import 'dart:convert';
import 'package:http/http.dart' as http;

String mapCategoryToBackend(String uiCategory) {
  const mapping = {
    "Shirt": "shirt",
    "T-Shirt": "tshirt",
    "Pants": "trouser",
    "Jeans": "jeans",
    "Dress": "dress",
    "Saree": "saree",
    "Jacket": "jacket",
    "Sweater": "other",   // no dedicated backend category yet
    "Kids Wear": "other", // no dedicated backend category yet
    "Blanket": "blanket",
    "Other": "other",
  };
  return mapping[uiCategory] ?? "other";
}

class ReWearApiService {
  // Android emulator: 10.0.2.2 points back to your PC (localhost won't work here)
  // Real phone on same WiFi: use your PC's actual IP, e.g. http://192.168.1.42:8000/api/v1
  static const String baseUrl = "http://10.0.2.2:8000/api/v1";

  Future<String> createDonation({
    required String donorId,
    required String category,
    required String imageUrl,
    String? description,
  }) async {
    final response = await http.post(
      Uri.parse("$baseUrl/donations"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "donor_id": donorId,
        "category": category,
        "image_url": imageUrl,
        "description": description,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      return data["donation_id"];
    }
    throw Exception("Failed to create donation: ${response.statusCode} ${response.body}");
  }

  Future<Map<String, dynamic>> runPrediction(String donationId) async {
    final response = await http.post(
      Uri.parse("$baseUrl/donations/$donationId/predict"),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 503) {
      throw Exception("Quality check temporarily unavailable — model not deployed yet");
    }
    throw Exception("Prediction failed: ${response.statusCode} ${response.body}");
  }

  Future<Map<String, dynamic>> getRecommendations(String donationId) async {
    final response = await http.get(
      Uri.parse("$baseUrl/donations/$donationId/recommendations"),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception("Failed to get recommendations: ${response.statusCode} ${response.body}");
  }
}