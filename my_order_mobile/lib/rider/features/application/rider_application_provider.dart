import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/auth/auth_provider.dart';

/// State for the rider application flow (R8 apply form / R9 status).
class RiderApplicationState {
  final bool submitting;
  final String? error;
  final bool submitted;

  const RiderApplicationState({
    this.submitting = false,
    this.error,
    this.submitted = false,
  });

  RiderApplicationState copyWith({
    bool? submitting,
    String? error,
    bool? submitted,
  }) =>
      RiderApplicationState(
        submitting: submitting ?? this.submitting,
        error: error,
        submitted: submitted ?? this.submitted,
      );
}

class RiderApplicationController
    extends Notifier<RiderApplicationState> {
  @override
  RiderApplicationState build() => const RiderApplicationState();

  /// POST /riders/apply — NRC, license, vehicle plate.
  Future<void> submit({
    required String nrc,
    required String licenseNumber,
    required String vehiclePlate,
  }) async {
    state = state.copyWith(submitting: true, error: null);
    try {
      await ref.read(apiClientProvider).dio.post('/riders/apply', data: {
        'nrc': nrc.trim(),
        'license_number': licenseNumber.trim(),
        'vehicle_plate': vehiclePlate.trim(),
      });
      state = state.copyWith(submitting: false, submitted: true);
      // Refresh profile so rider_status becomes pending_review and the
      // AuthGate/home routing reflects the new state.
      await ref.read(authProvider.notifier).refreshProfile();
    } catch (e) {
      String msg = ApiClient.errorMessage(e);
      if (e is DioException && e.response?.statusCode == 400) {
        // Backend: "You already have a pending application"
        final detail = e.response?.data;
        if (detail is Map && detail['detail'] is String) {
          msg = detail['detail'] as String;
        }
      }
      state = state.copyWith(submitting: false, error: msg);
    }
  }
}

final riderApplicationProvider =
    NotifierProvider<RiderApplicationController, RiderApplicationState>(
  RiderApplicationController.new,
);
