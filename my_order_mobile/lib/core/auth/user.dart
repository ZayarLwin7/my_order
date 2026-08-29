/// User role, mirroring backend UserRole enum.
enum UserRole { sender, rider, admin, staff }

UserRole? roleFromString(String? value) {
  for (final r in UserRole.values) {
    if (r.name == value) return r;
  }
  return null;
}

/// Mirrors backend MeOut schema from GET /users/me.
class UserProfile {
  final String id;
  final String name;
  final String phone;
  final UserRole role;

  // Merchant/partner state (senders)
  final String partnerStatus; // none | pending_review | approved | rejected
  final String? partnerBusinessName;
  final bool isActivePartner;

  // Rider application state (riders)
  final String riderStatus; // none | pending_review | approved | rejected
  final bool isActiveRider;

  const UserProfile({
    required this.id,
    required this.name,
    required this.phone,
    required this.role,
    required this.partnerStatus,
    this.partnerBusinessName,
    this.isActivePartner = false,
    this.riderStatus = 'none',
    this.isActiveRider = false,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      name: json['name'] as String,
      phone: json['phone'] as String,
      role: roleFromString(json['role'] as String?) ?? UserRole.sender,
      partnerStatus: (json['partner_status'] ?? 'none') as String,
      partnerBusinessName: json['partner_business_name'] as String?,
      isActivePartner: (json['is_active_partner'] ?? false) as bool,
      riderStatus: (json['rider_status'] ?? 'none') as String,
      isActiveRider: (json['is_active_rider'] ?? false) as bool,
    );
  }
}
