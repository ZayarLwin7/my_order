import 'package:flutter/material.dart';

import 'theme/colors.dart';

/// Which flavor of the app is running.
enum AppFlavor { customer, rider, staff, admin }

/// Per-flavor identity: names, icons, colors, and the single backend role
/// each app accepts at login (Section 1A of FLUTTER_DESIGN.md).
class FlavorConfig {
  final AppFlavor flavor;
  final String appName;
  final String tagline;
  final IconData icon;
  final Color brandColor;
  final String allowedRole;
  final String wrongRoleMessage;

  const FlavorConfig({
    required this.flavor,
    required this.appName,
    required this.tagline,
    required this.icon,
    required this.brandColor,
    required this.allowedRole,
    required this.wrongRoleMessage,
  });

  static const customer = FlavorConfig(
    flavor: AppFlavor.customer,
    appName: 'My Order',
    tagline: 'Send parcels across Myanmar',
    icon: Icons.local_shipping_rounded,
    brandColor: MOColors.senderColor,
    allowedRole: 'sender',
    wrongRoleMessage:
        'This is not a customer account.\nPlease use the My Order Rider or Staff app.',
  );

  static const rider = FlavorConfig(
    flavor: AppFlavor.rider,
    appName: 'My Order Rider',
    tagline: 'Deliver parcels and earn per completed way',
    icon: Icons.two_wheeler_rounded,
    brandColor: MOColors.riderColor,
    allowedRole: 'rider',
    wrongRoleMessage:
        'This is not a rider account.\nPlease use the My Order customer app.',
  );

  static const staff = FlavorConfig(
    flavor: AppFlavor.staff,
    appName: 'My Order Staff',
    tagline: 'Office walk-in order creation',
    icon: Icons.business_center_rounded,
    brandColor: MOColors.staffColor,
    allowedRole: 'staff',
    wrongRoleMessage:
        'This is not a staff account.\nStaff accounts are provisioned by your administrator.',
  );

  static const admin = FlavorConfig(
    flavor: AppFlavor.admin,
    appName: 'My Order Admin',
    tagline: 'Operations dashboard',
    icon: Icons.admin_panel_settings,
    brandColor: MOColors.adminColor,
    allowedRole: 'admin',
    wrongRoleMessage:
        'Admin access required.\nThis account is not an admin.',
  );
}
