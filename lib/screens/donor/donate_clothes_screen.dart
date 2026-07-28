import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:uuid/uuid.dart';

import '../../models/donation_model.dart';
import '../../services/donation_service.dart';
import '../../services/storage_service.dart';
import '../../services/api_service.dart';

class DonateClothesScreen extends StatefulWidget {
  const DonateClothesScreen({super.key});

  @override
  State<DonateClothesScreen> createState() =>
      _DonateClothesScreenState();
}

class _DonateClothesScreenState
    extends State<DonateClothesScreen> {
  bool isLoading = false;
  // -------------------------------------------------
  // Image Picker
  // -------------------------------------------------
  final StorageService _storageService = StorageService();
  final DonationService _donationService = DonationService();
  final ReWearApiService _apiService = ReWearApiService();
  final ImagePicker _picker = ImagePicker();

  Map<String, dynamic>? aiQualityReport;
  Map<String, dynamic>? aiRecommendations;

  List<File> selectedImages = [];

  // -------------------------------------------------
  // Controllers
  // -------------------------------------------------

  final TextEditingController descriptionController =
      TextEditingController();

  final TextEditingController addressController =
      TextEditingController();

  // -------------------------------------------------
  // Dropdown Values
  // -------------------------------------------------

  String? selectedCategory;
  String? selectedGender;
  String? selectedAgeGroup;
  String? selectedSize;
  String? selectedColor;
  String? selectedCondition;
  String? selectedNgo;
  String? selectedTimeSlot;

  DateTime? pickupDate;

  int quantity = 1;

  bool washed = false;
  bool ironed = false;
  bool minorDamage = false;

  // -------------------------------------------------
  // Lists
  // -------------------------------------------------

  final List<String> categories = [
    "Shirt",
    "T-Shirt",
    "Pants",
    "Jeans",
    "Dress",
    "Saree",
    "Jacket",
    "Sweater",
    "Kids Wear",
    "Blanket",
    "Other",
  ];

  final List<String> genders = [
    "Men",
    "Women",
    "Unisex",
    "Kids",
  ];

  final List<String> ageGroups = [
    "Baby",
    "Child",
    "Teen",
    "Adult",
    "Senior",
  ];

  final List<String> sizes = [
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
    "Free Size",
  ];

  final List<String> colors = [
    "Black",
    "White",
    "Blue",
    "Red",
    "Green",
    "Yellow",
    "Pink",
    "Grey",
    "Brown",
    "Multi Color",
  ];

  final List<String> conditions = [
    "Excellent",
    "Good",
    "Fair",
  ];

  final List<String> ngos = [
    "Any Nearby NGO",
    "Children's Home",
    "Old Age Home",
    "Women Shelter",
    "Orphanage",
  ];

  final List<String> timeSlots = [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
  ];

  // -------------------------------------------------
  // Pick Images From Gallery
  // -------------------------------------------------

  Future<void> pickImages() async {

    final List<XFile> images =
        await _picker.pickMultiImage(
      imageQuality: 70,
    );

    if (images.isNotEmpty) {

      setState(() {

        selectedImages
            .addAll(images.map((e) => File(e.path)));

      });

    }

  }

  // -------------------------------------------------
  // Pick Image From Camera
  // -------------------------------------------------

  Future<void> pickCameraImage() async {

    final XFile? image =
        await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 70,
    );

    if (image != null) {

      setState(() {

        selectedImages.add(
          File(image.path),
        );

      });

    }

  }

  // -------------------------------------------------
  // Remove Image
  // -------------------------------------------------

  void removeImage(int index) {

    setState(() {

      selectedImages.removeAt(index);

    });

  }

  // -------------------------------------------------
  // Select Pickup Date
  // -------------------------------------------------

  Future<void> selectPickupDate() async {

    DateTime? picked =
        await showDatePicker(

      context: context,

      initialDate: DateTime.now(),

      firstDate: DateTime.now(),

      lastDate: DateTime(2035),

    );

    if (picked != null) {

      setState(() {

        pickupDate = picked;

      });

    }

  }

  // -------------------------------------------------
  // Submit Donation
  // -------------------------------------------------

Future<void> submitDonation() async {

  if (selectedImages.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Please select at least one image."),
      ),
    );
    return;
  }

  if (selectedCategory == null ||
      selectedSize == null ||
      selectedCondition == null ||
      pickupDate == null ||
      addressController.text.trim().isEmpty ||
      descriptionController.text.trim().isEmpty) {

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Please fill all required fields."),
      ),
    );
    return;
  }

  setState(() {
    isLoading = true;
  });

  try {

    final user = FirebaseAuth.instance.currentUser!;

    List<String> imageUrls =
        await _storageService.uploadImages(selectedImages);

    // --- ReWear AI quality check (non-blocking: donation still saves even if this fails) ---
    try {
      final backendCategory = mapCategoryToBackend(selectedCategory!);
      final beDonationId = await _apiService.createDonation(
        donorId: user.uid,
        category: backendCategory,
        imageUrl: imageUrls.first,
        description: descriptionController.text.trim(),
      );
      final report = await _apiService.runPrediction(beDonationId);
      Map<String, dynamic>? recs;
      if (report["decision"] != "accept") {
        recs = await _apiService.getRecommendations(beDonationId);
      }
      setState(() {
        aiQualityReport = report;
        aiRecommendations = recs;
      });
    } catch (e) {
      debugPrint("AI quality check failed (non-blocking): $e");
    }

    String donationId = const Uuid().v4();

    DonationModel donation = DonationModel(

      donationId: donationId,

      donorId: user.uid,

      donorName: user.email ?? "Donor",

      category: selectedCategory!,

      size: selectedSize!,

      condition: selectedCondition!,

      description: descriptionController.text.trim(),

      address: addressController.text.trim(),

      pickupDate: pickupDate.toString(),

      imageUrls: imageUrls,

      status: "Pending",

      ngoId: "",

      createdAt: DateTime.now(),

    );

    String? result =
        await _donationService.addDonation(donation);

    setState(() {
      isLoading = false;
    });

    if (result == null) {

      ScaffoldMessenger.of(context).showSnackBar(

        const SnackBar(
          backgroundColor: Colors.green,
          content: Text("Donation Submitted Successfully"),
        ),

      );

      if (aiQualityReport != null) {
        await showDialog(
          context: context,
          builder: (_) => AlertDialog(
            title: const Text("AI Quality Check"),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Score: ${aiQualityReport!['quality_score']}"),
                Text("Decision: ${aiQualityReport!['decision']}"),
                if (aiRecommendations != null &&
                    (aiRecommendations!['suggestions'] as List).isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Text(
                      "Suggestions: ${(aiRecommendations!['suggestions'] as List).map((s) => s['product_name']).join(', ')}",
                    ),
                  ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text("OK"),
              ),
            ],
          ),
        );
      }

      Navigator.pop(context);

    } else {

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result)),
      );

    }

  } catch (e) {

    setState(() {
      isLoading = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(e.toString())),
    );

  }

} 

  @override
  Widget build(BuildContext context) {
        return Scaffold(
      backgroundColor: const Color(0xffF5F7FA),

      appBar: AppBar(
        elevation: 0,
        backgroundColor: const Color(0xff2E7D32),
        foregroundColor: Colors.white,
        title: const Text(
          "Donate Clothes",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),

          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              const Text(
                "Upload Images",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 15),

              Row(
                children: [

                  Expanded(
                    child: ElevatedButton.icon(

                      onPressed: pickCameraImage,

                      icon: const Icon(Icons.camera_alt),

                      label: const Text("Camera"),

                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xff2E7D32),
                        foregroundColor: Colors.white,
                        minimumSize: const Size.fromHeight(50),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(15),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(width: 15),

                  Expanded(
                    child: ElevatedButton.icon(

                      onPressed: pickImages,

                      icon: const Icon(Icons.photo_library),

                      label: const Text("Gallery"),

                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                        minimumSize: const Size.fromHeight(50),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(15),
                        ),
                      ),
                    ),
                  ),

                ],
              ),

              const SizedBox(height: 20),

              selectedImages.isEmpty

                  ?

              Container(

                height: 180,

                width: double.infinity,

                decoration: BoxDecoration(

                  color: Colors.white,

                  borderRadius:
                      BorderRadius.circular(20),

                  border: Border.all(
                    color: Colors.grey.shade300,
                  ),

                ),

                child: const Column(

                  mainAxisAlignment:
                      MainAxisAlignment.center,

                  children: [

                    Icon(
                      Icons.image_outlined,
                      size: 60,
                      color: Colors.grey,
                    ),

                    SizedBox(height: 10),

                    Text(
                      "No Images Selected",
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),

                  ],

                ),

              )

                  :

              GridView.builder(

                shrinkWrap: true,

                physics:
                    const NeverScrollableScrollPhysics(),

                itemCount: selectedImages.length,

                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(

                  crossAxisCount: 3,

                  crossAxisSpacing: 10,

                  mainAxisSpacing: 10,

                ),

                itemBuilder: (context, index) {

                  return Stack(

                    children: [

                      ClipRRect(

                        borderRadius:
                            BorderRadius.circular(15),

                        child: Image.file(

                          selectedImages[index],

                          width: double.infinity,

                          height: double.infinity,

                          fit: BoxFit.cover,

                        ),

                      ),

                      Positioned(

                        top: 5,

                        right: 5,

                        child: InkWell(

                          onTap: () {

                            removeImage(index);

                          },

                          child: Container(

                            decoration:
                                const BoxDecoration(

                              color: Colors.red,

                              shape: BoxShape.circle,

                            ),

                            padding:
                                const EdgeInsets.all(4),

                            child: const Icon(

                              Icons.close,

                              size: 18,

                              color: Colors.white,

                            ),

                          ),

                        ),

                      ),

                    ],

                  );

                },

              ),

              const SizedBox(height: 30),
                            Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),

                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,

                    children: [

                      const Text(
                        "Clothing Details",
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(
                        initialValue: selectedCategory,
                        decoration: InputDecoration(
                          labelText: "Category",
                          prefixIcon: const Icon(Icons.checkroom),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                        items: categories.map((item) {
                          return DropdownMenuItem(
                            value: item,
                            child: Text(item),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedCategory = value;
                          });
                        },
                      ),

                      const SizedBox(height: 18),

                      DropdownButtonFormField<String>(
                        initialValue: selectedGender,
                        decoration: InputDecoration(
                          labelText: "Gender",
                          prefixIcon: const Icon(Icons.people),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                        items: genders.map((item) {
                          return DropdownMenuItem(
                            value: item,
                            child: Text(item),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedGender = value;
                          });
                        },
                      ),

                      const SizedBox(height: 18),

                      DropdownButtonFormField<String>(
                        initialValue: selectedAgeGroup,
                        decoration: InputDecoration(
                          labelText: "Age Group",
                          prefixIcon: const Icon(Icons.child_care),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                        items: ageGroups.map((item) {
                          return DropdownMenuItem(
                            value: item,
                            child: Text(item),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedAgeGroup = value;
                          });
                        },
                      ),

                      const SizedBox(height: 18),

                      Row(
                        children: [

                          Expanded(
                            child: DropdownButtonFormField<String>(
                              initialValue: selectedSize,
                              decoration: InputDecoration(
                                labelText: "Size",
                                prefixIcon:
                                    const Icon(Icons.straighten),
                                border: OutlineInputBorder(
                                  borderRadius:
                                      BorderRadius.circular(15),
                                ),
                              ),
                              items: sizes.map((item) {
                                return DropdownMenuItem(
                                  value: item,
                                  child: Text(item),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() {
                                  selectedSize = value;
                                });
                              },
                            ),
                          ),

                          const SizedBox(width: 15),

                          Expanded(
                            child: DropdownButtonFormField<String>(
                              initialValue: selectedColor,
                              decoration: InputDecoration(
                                labelText: "Color",
                                prefixIcon:
                                    const Icon(Icons.palette),
                                border: OutlineInputBorder(
                                  borderRadius:
                                      BorderRadius.circular(15),
                                ),
                              ),
                              items: colors.map((item) {
                                return DropdownMenuItem(
                                  value: item,
                                  child: Text(item),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() {
                                  selectedColor = value;
                                });
                              },
                            ),
                          ),

                        ],
                      ),

                      const SizedBox(height: 25),

                      const Text(
                        "Quantity",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 17,
                        ),
                      ),

                      const SizedBox(height: 12),

                      Container(
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius:
                              BorderRadius.circular(15),
                        ),
                        padding:
                            const EdgeInsets.symmetric(
                          horizontal: 15,
                          vertical: 10,
                        ),

                        child: Row(
                          mainAxisAlignment:
                              MainAxisAlignment.spaceBetween,

                          children: [

                            IconButton(
                              onPressed: () {
                                if (quantity > 1) {
                                  setState(() {
                                    quantity--;
                                  });
                                }
                              },
                              icon: const Icon(
                                Icons.remove_circle,
                                color: Colors.red,
                                size: 32,
                              ),
                            ),

                            Text(
                              quantity.toString(),
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            IconButton(
                              onPressed: () {
                                setState(() {
                                  quantity++;
                                });
                              },
                              icon: const Icon(
                                Icons.add_circle,
                                color: Color(0xff2E7D32),
                                size: 32,
                              ),
                            ),

                          ],
                        ),
                      ),

                    ],
                  ),
                ),
              ),

              const SizedBox(height: 30),
                            Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [

                      const Text(
                        "Clothing Condition",
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(
                        initialValue: selectedCondition,
                        decoration: InputDecoration(
                          labelText: "Condition",
                          prefixIcon: const Icon(Icons.star),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                        items: conditions.map((item) {
                          return DropdownMenuItem(
                            value: item,
                            child: Text(item),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedCondition = value;
                          });
                        },
                      ),

                      const SizedBox(height: 20),

                      CheckboxListTile(
                        value: washed,
                        activeColor: const Color(0xff2E7D32),
                        title: const Text("Washed"),
                        secondary: const Icon(Icons.local_laundry_service),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(15),
                        ),
                        onChanged: (value) {
                          setState(() {
                            washed = value!;
                          });
                        },
                      ),

                      CheckboxListTile(
                        value: ironed,
                        activeColor: const Color(0xff2E7D32),
                        title: const Text("Ironed"),
                        secondary: const Icon(Icons.iron),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(15),
                        ),
                        onChanged: (value) {
                          setState(() {
                            ironed = value!;
                          });
                        },
                      ),

                      CheckboxListTile(
                        value: minorDamage,
                        activeColor: Colors.red,
                        title: const Text("Minor Damage"),
                        secondary: const Icon(Icons.build),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(15),
                        ),
                        onChanged: (value) {
                          setState(() {
                            minorDamage = value!;
                          });
                        },
                      ),

                      const SizedBox(height: 25),

                      TextField(
                        controller: descriptionController,
                        maxLines: 5,
                        decoration: InputDecoration(
                          labelText: "Description",
                          hintText:
                              "Describe the clothes, brand, fabric, age, or any additional details...",
                          alignLabelWithHint: true,
                          prefixIcon: const Padding(
                            padding: EdgeInsets.only(bottom: 90),
                            child: Icon(Icons.description),
                          ),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                      ),

                    ],
                  ),
                ),
              ),

              const SizedBox(height: 30),
                            Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [

                      const Text(
                        "Pickup Details",
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: addressController,
                        maxLines: 2,
                        decoration: InputDecoration(
                          labelText: "Pickup Address",
                          hintText: "Enter complete pickup address",
                          prefixIcon: const Icon(Icons.location_on),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(15),
                          ),
                        ),
                      ),

                      const SizedBox(height: 15),

                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(

                          onPressed: () {

                            ScaffoldMessenger.of(context).showSnackBar(

                              const SnackBar(
                                content: Text(
                                  "Current Location feature will be added with GPS integration.",
                                ),
                              ),

                            );

                          },

                          icon: const Icon(Icons.my_location),

                          label: const Text(
                            "Use Current Location",
                          ),

                          style: OutlinedButton.styleFrom(
                            minimumSize: const Size.fromHeight(50),
                            foregroundColor: const Color(0xff2E7D32),
                            side: const BorderSide(
                              color: Color(0xff2E7D32),
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(15),
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 20),

                      InkWell(

                        onTap: selectPickupDate,

                        borderRadius: BorderRadius.circular(15),

                        child: Container(

                          width: double.infinity,

                          padding: const EdgeInsets.all(16),

                          decoration: BoxDecoration(

                            border: Border.all(
                              color: Colors.grey.shade400,
                            ),

                            borderRadius:
                                BorderRadius.circular(15),

                          ),

                          child: Row(

                            children: [

                              const Icon(
                                Icons.calendar_month,
                                color: Color(0xff2E7D32),
                              ),

                              const SizedBox(width: 12),

                              Expanded(

                                child: Text(

                                  pickupDate == null
                                      ? "Select Pickup Date"
                                      : "${pickupDate!.day}/${pickupDate!.month}/${pickupDate!.year}",

                                  style: const TextStyle(
                                    fontSize: 16,
                                  ),

                                ),

                              ),

                              const Icon(Icons.arrow_drop_down),

                            ],

                          ),

                        ),

                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(

                        initialValue: selectedTimeSlot,

                        decoration: InputDecoration(

                          labelText: "Pickup Time",

                          prefixIcon:
                              const Icon(Icons.access_time),

                          border: OutlineInputBorder(

                            borderRadius:
                                BorderRadius.circular(15),

                          ),

                        ),

                        items: timeSlots.map((slot) {

                          return DropdownMenuItem(

                            value: slot,

                            child: Text(slot),

                          );

                        }).toList(),

                        onChanged: (value) {

                          setState(() {

                            selectedTimeSlot = value;

                          });

                        },

                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(

                        initialValue: selectedNgo,

                        decoration: InputDecoration(

                          labelText: "Preferred NGO",

                          prefixIcon:
                              const Icon(Icons.business),

                          border: OutlineInputBorder(

                            borderRadius:
                                BorderRadius.circular(15),

                          ),

                        ),

                        items: ngos.map((ngo) {

                          return DropdownMenuItem(

                            value: ngo,

                            child: Text(ngo),

                          );

                        }).toList(),

                        onChanged: (value) {

                          setState(() {

                            selectedNgo = value;

                          });

                        },

                      ),

                    ],
                  ),
                ),
              ),

              const SizedBox(height: 30),

              // =====================================================
              // Submit Button
              // =====================================================

              SizedBox(
                width: double.infinity,
                height: 60,
                child: ElevatedButton.icon(

                  onPressed: isLoading ? null : submitDonation,

                  icon: const Icon(Icons.volunteer_activism),

                  
label: isLoading
    ? const SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(
          strokeWidth: 3,
          color: Colors.white,
        ),
      )
    : const Text(
        "Submit Donation",
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xff2E7D32),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(18),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 30),

            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    descriptionController.dispose();
    addressController.dispose();
    super.dispose();
  }
}