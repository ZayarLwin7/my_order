import 'package:flutter/material.dart';

import '../theme/colors.dart';

/// Renders an order status as a colored chip.
///
/// Maps backend OrderStatus -> color + label.
class MOStatusBadge extends StatelessWidget {
  final String status;
  final bool compact;

  const MOStatusBadge({super.key, required this.status, this.compact = false});

  static Color _colorFor(String status) {
    switch (status) {
      case 'pending':
        return MOColors.statusPending;
      case 'assigned':
        return MOColors.statusAssigned;
      case 'picked_up':
        return MOColors.statusInTransit;
      case 'delivered':
        return MOColors.statusDelivered;
      case 'dropped_at_terminal':
        return MOColors.statusTerminal;
      case 'delivery_failed':
        return MOColors.statusFailed;
      case 'disputed':
        return MOColors.statusDisputed;
      case 'cancelled':
      case 'cancelled_post_pickup':
      case 'returned':
        return MOColors.statusCancelled;
      default:
        return MOColors.statusCancelled;
    }
  }

  static String _labelFor(String status) {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'assigned':
        return 'Assigned';
      case 'picked_up':
        return 'In Transit';
      case 'delivered':
        return 'Delivered';
      case 'dropped_at_terminal':
        return 'At Terminal';
      case 'delivery_failed':
        return 'Failed';
      case 'disputed':
        return 'Disputed';
      case 'cancelled':
        return 'Cancelled';
      case 'cancelled_post_pickup':
        return 'Cancelled';
      case 'returned':
        return 'Returned';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _colorFor(status);
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 12,
        vertical: compact ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        _labelFor(status),
        style: TextStyle(
          color: color,
          fontSize: compact ? 11 : 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
