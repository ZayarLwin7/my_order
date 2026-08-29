import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/secure_storage.dart';

/// Backend base URL.
///
/// Platform-aware defaults:
/// - Web (admin dashboard) -> localhost (runs on the same machine as backend)
/// - Android emulator       -> 10.0.2.2 (host loopback alias)
/// - iOS simulator/desktop  -> localhost
/// - Physical device        -> override with --dart-define=API_BASE_URL=http://your-mac-lan-ip:8000/api/v1
const String _kDefaultBaseUrl = kIsWeb
    ? 'http://localhost:8000/api/v1'
    : 'http://10.0.2.2:8000/api/v1';

const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: _kDefaultBaseUrl,
);

/// Dio client with JWT attach + 401 handling.
class ApiClient {
  final Dio dio = Dio();
  final TokenStorage _tokenStorage;

  ApiClient(this._tokenStorage) {
    dio.options
      ..baseUrl = kApiBaseUrl
      ..connectTimeout = const Duration(seconds: 15)
      ..receiveTimeout = const Duration(seconds: 20)
      ..headers['Content-Type'] = 'application/json';

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _tokenStorage.read();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // Invalid/expired token -> clear it so AuthGate forces re-login.
        if (error.response?.statusCode == 401) {
          await _tokenStorage.clear();
        }
        handler.next(error);
      },
    ));
  }

  /// Extracts the backend's {"detail": "..."} message from an error response.
  static String errorMessage(Object error) {
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map && data['detail'] is String) {
        return data['detail'] as String;
      }
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.receiveTimeout:
          return 'Connection timed out. Please try again.';
        case DioExceptionType.connectionError:
          return 'Cannot reach the server. Check your connection.';
        default:
          return 'Something went wrong. Please try again.';
      }
    }
    return 'Something went wrong. Please try again.';
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(tokenStorageProvider));
});
