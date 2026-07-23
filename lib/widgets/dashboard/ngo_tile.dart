import 'package:flutter/material.dart';

class NgoTile extends StatelessWidget {
  final String ngoName;
  final String distance;
  final double rating;
  final VoidCallback onTap;

  const NgoTile({
    super.key,
    required this.ngoName,
    required this.distance,
    required this.rating,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),

      child: Container(
        width: 190,

        margin: const EdgeInsets.only(right: 16),

        padding: const EdgeInsets.all(14),

        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),

          boxShadow: [
            BoxShadow(
              color: Colors.grey.shade200,
              blurRadius: 10,
              offset: const Offset(0, 5),
            ),
          ],
        ),

        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            Container(
              padding: const EdgeInsets.all(8),

              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(12),
              ),

              child: const Icon(
                Icons.business,
                color: Color(0xff2E7D32),
                size: 24,
              ),
            ),


            const SizedBox(height: 10),


            Text(
              ngoName,

              maxLines: 1,
              overflow: TextOverflow.ellipsis,

              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),


            const SizedBox(height: 5),


            Row(
              children: [

                const Icon(
                  Icons.star,
                  color: Colors.orange,
                  size: 16,
                ),

                const SizedBox(width: 4),

                Text(
                  rating.toString(),

                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ],
            ),


            const SizedBox(height: 5),


            Row(
              children: [

                const Icon(
                  Icons.location_on,
                  color: Colors.red,
                  size: 16,
                ),

                const SizedBox(width: 3),

                Expanded(
                  child: Text(
                    distance,

                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,

                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}