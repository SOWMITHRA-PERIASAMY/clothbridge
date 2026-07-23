class DonationModel {
  final String donationId;
  final String donorId;
  final String donorName;
  final String category;
  final String size;
  final String condition;
  final String description;
  final String address;
  final String pickupDate;
  final List<String> imageUrls;
  final String status;
  final String ngoId;
  final DateTime createdAt;

  DonationModel({
    required this.donationId,
    required this.donorId,
    required this.donorName,
    required this.category,
    required this.size,
    required this.condition,
    required this.description,
    required this.address,
    required this.pickupDate,
    required this.imageUrls,
    required this.status,
    required this.ngoId,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'donationId': donationId,
      'donorId': donorId,
      'donorName': donorName,
      'category': category,
      'size': size,
      'condition': condition,
      'description': description,
      'address': address,
      'pickupDate': pickupDate,
      'imageUrls': imageUrls,
      'status': status,
      'ngoId': ngoId,
      'createdAt': createdAt,
    };
  }

  factory DonationModel.fromMap(Map<String, dynamic> map) {
    return DonationModel(
      donationId: map['donationId'],
      donorId: map['donorId'],
      donorName: map['donorName'],
      category: map['category'],
      size: map['size'],
      condition: map['condition'],
      description: map['description'],
      address: map['address'],
      pickupDate: map['pickupDate'],
      imageUrls: List<String>.from(map['imageUrls']),
      status: map['status'],
      ngoId: map['ngoId'],
      createdAt: map['createdAt'].toDate(),
    );
  }
}