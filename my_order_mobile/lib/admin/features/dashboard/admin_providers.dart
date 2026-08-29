import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

/// A pending rider application (matches RiderApplicationOut).
class RiderApplicationItem {
  final String id;
  final String nrc;
  final String licenseNumber;
  final String vehiclePlate;
  final String status;
  final String submittedAt;

  const RiderApplicationItem({
    required this.id,
    required this.nrc,
    required this.licenseNumber,
    required this.vehiclePlate,
    required this.status,
    required this.submittedAt,
  });

  factory RiderApplicationItem.fromJson(Map<String, dynamic> json) =>
      RiderApplicationItem(
        id: json['id'] as String,
        nrc: (json['nrc'] ?? '') as String,
        licenseNumber: (json['license_number'] ?? '') as String,
        vehiclePlate: (json['vehicle_plate'] ?? '') as String,
        status: (json['status'] ?? '') as String,
        submittedAt: (json['submitted_at'] ?? '') as String,
      );
}

/// An assignable rider (matches ActiveRiderOut).
class ActiveRiderItem {
  final String userId;
  final String name;
  final String phone;

  const ActiveRiderItem({required this.userId, required this.name, required this.phone});

  factory ActiveRiderItem.fromJson(Map<String, dynamic> json) => ActiveRiderItem(
        userId: json['user_id'] as String,
        name: (json['name'] ?? '') as String,
        phone: (json['phone'] ?? '') as String,
      );
}

/// A pending order (matches OrderOut).
class AdminOrderItem {
  final String id;
  final String recipientName;
  final String recipientPhone;
  final String status;
  final String pickupAddress;
  final String dropoffAddress;
  final String itemValue;
  final String fee;
  final bool isWalkin;

  const AdminOrderItem({
    required this.id,
    required this.recipientName,
    required this.recipientPhone,
    required this.status,
    required this.pickupAddress,
    required this.dropoffAddress,
    required this.itemValue,
    required this.fee,
    required this.isWalkin,
  });

  factory AdminOrderItem.fromJson(Map<String, dynamic> json) => AdminOrderItem(
        id: json['id'] as String,
        recipientName: (json['recipient_name'] ?? '') as String,
        recipientPhone: (json['recipient_phone'] ?? '') as String,
        status: (json['status'] ?? '') as String,
        pickupAddress: (json['pickup_address'] ?? '') as String,
        dropoffAddress: (json['dropoff_address'] ?? '-') as String,
        itemValue: (json['item_value'] ?? '0').toString(),
        fee: (json['delivery_fee'] ?? '0').toString(),
        isWalkin: (json['is_walkin'] ?? false) as bool,
      );
}

/// State for the admin dashboard lists + actions.
class AdminDashboardState {
  final bool loading;
  final String? error;
  final List<RiderApplicationItem> riderApplications;
  final List<AdminOrderItem> pendingOrders;
  final List<ActiveRiderItem> activeRiders;
  final String? actionError;

  const AdminDashboardState({
    this.loading = true,
    this.error,
    this.riderApplications = const [],
    this.pendingOrders = const [],
    this.activeRiders = const [],
    this.actionError,
  });

  AdminDashboardState copyWith({
    bool? loading,
    String? error,
    List<RiderApplicationItem>? riderApplications,
    List<AdminOrderItem>? pendingOrders,
    List<ActiveRiderItem>? activeRiders,
    String? actionError,
  }) =>
      AdminDashboardState(
        loading: loading ?? this.loading,
        error: error,
        riderApplications: riderApplications ?? this.riderApplications,
        pendingOrders: pendingOrders ?? this.pendingOrders,
        activeRiders: activeRiders ?? this.activeRiders,
        actionError: actionError,
      );
}

class AdminDashboardController extends Notifier<AdminDashboardState> {
  @override
  AdminDashboardState build() {
    _load();
    return const AdminDashboardState();
  }

  Future<void> _load() async {
    state = const AdminDashboardState(loading: true);
    final api = ref.read(apiClientProvider);
    try {
      final results = await Future.wait([
        api.dio.get('/riders/applications'),
        api.dio.get('/orders?status=pending'),
        api.dio.get('/riders/active'),
      ]);
      state = AdminDashboardState(
        loading: false,
        riderApplications: (results[0].data as List)
            .map((e) => RiderApplicationItem.fromJson(e))
            .toList(),
        pendingOrders: (results[1].data as List)
            .map((e) => AdminOrderItem.fromJson(e))
            .toList(),
        activeRiders: (results[2].data as List)
            .map((e) => ActiveRiderItem.fromJson(e))
            .toList(),
      );
    } catch (e) {
      state = state.copyWith(loading: false, error: ApiClient.errorMessage(e));
    }
  }

  Future<void> refresh() => _load();

  Future<void> approveApplication(String applicationId) async {
    await _review(applicationId, approve: true);
  }

  Future<void> rejectApplication(String applicationId) async {
    await _review(applicationId, approve: false);
  }

  Future<void> _review(String applicationId, {required bool approve}) async {
    final api = ref.read(apiClientProvider);
    try {
      await api.dio.patch(
        '/riders/$applicationId/${approve ? 'approve' : 'reject'}',
        data: {},
      );
      await _load();
    } catch (e) {
      state = state.copyWith(actionError: ApiClient.errorMessage(e));
    }
  }

  Future<void> assignOrder(String orderId, String riderId) async {
    final api = ref.read(apiClientProvider);
    try {
      await api.dio.patch('/orders/$orderId/assign', data: {'rider_id': riderId});
      await _load();
    } catch (e) {
      state = state.copyWith(actionError: ApiClient.errorMessage(e));
    }
  }
}

final adminDashboardProvider =
    NotifierProvider<AdminDashboardController, AdminDashboardState>(
  AdminDashboardController.new,
);
