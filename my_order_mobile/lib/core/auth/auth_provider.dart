import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../storage/secure_storage.dart';
import 'user.dart';

/// Auth states for the AuthGate.
enum AuthStatus { loading, unauthenticated, authenticated }

class AuthState {
  final AuthStatus status;
  final UserProfile? profile;

  const AuthState({required this.status, this.profile});

  const AuthState.loading() : this(status: AuthStatus.loading);
  const AuthState.unauthenticated() : this(status: AuthStatus.unauthenticated);
}

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    _bootstrap();
    return const AuthState.loading();
  }

  Future<void> _bootstrap() async {
    final api = ref.read(apiClientProvider);
    final storage = ref.read(tokenStorageProvider);

    final token = await storage.read();
    if (token == null) {
      state = const AuthState.unauthenticated();
      return;
    }

    // Token exists -> validate by fetching the profile.
    try {
      final res = await api.dio.get('/users/me');
      state = AuthState(
        status: AuthStatus.authenticated,
        profile: UserProfile.fromJson(res.data as Map<String, dynamic>),
      );
    } catch (_) {
      await storage.clear();
      state = const AuthState.unauthenticated();
    }
  }

  /// POST /auth/login then load profile.
  Future<String?> login(String phone, String password) async {
    final api = ref.read(apiClientProvider);
    final storage = ref.read(tokenStorageProvider);
    try {
      final res = await api.dio.post('/auth/login', data: {
        'phone': phone.trim(),
        'password': password,
      });
      await storage.write(res.data['access_token'] as String);
      await refreshProfile();
      return null; // success
    } catch (e) {
      return ApiClient.errorMessage(e);
    }
  }

  /// POST /auth/register (sender or rider only, per backend).
  Future<String?> register({
    required String name,
    required String phone,
    required String password,
    required UserRole role,
  }) async {
    final api = ref.read(apiClientProvider);
    try {
      await api.dio.post('/auth/register', data: {
        'name': name.trim(),
        'phone': phone.trim(),
        'password': password,
        'role': role.name,
      });
      // Auto-login after successful registration.
      return await login(phone, password);
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 422) {
        return 'Please check your details (password needs 12+ characters).';
      }
      if (e is DioException && e.response?.statusCode == 400) {
        final detail = e.response?.data;
        if (detail is Map && detail['detail'] is String) {
          return detail['detail'] as String; // e.g. "Phone number already registered"
        }
      }
      return ApiClient.errorMessage(e);
    }
  }

  /// GET /users/me to refresh partner status etc.
  Future<void> refreshProfile() async {
    try {
      final res = await ref.read(apiClientProvider).dio.get('/users/me');
      state = AuthState(
        status: AuthStatus.authenticated,
        profile: UserProfile.fromJson(res.data as Map<String, dynamic>),
      );
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 401) {
        await logout();
      }
    }
  }

  Future<void> logout() async {
    await ref.read(tokenStorageProvider).clear();
    state = const AuthState.unauthenticated();
  }
}

final authProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);
