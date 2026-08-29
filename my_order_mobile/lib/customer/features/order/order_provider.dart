import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

/// Thrown when the backend rejects a quote/order request.
class OrderApiException implements Exception {
  final String message;
  OrderApiException(this.message);
  @override
  String toString() => message;
}

/// Raw API access for the customer order flow (Phase 2).
/// Matches the backend `/quotes` and `/orders` contracts.
class OrderApi {
  final ApiClient _client;
  OrderApi(this._client);

  /// POST /quotes -> returns the quote map (incl. id, fees, expires_at).
  Future<Map<String, dynamic>> requestQuote(Map<String, dynamic> payload) async {
    try {
      final res = await _client.dio.post('/quotes', data: payload);
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw OrderApiException(ApiClient.errorMessage(e));
    }
  }

  /// POST /orders -> returns the created order map (incl. id, status).
  Future<Map<String, dynamic>> createOrder(Map<String, dynamic> payload) async {
    try {
      final res = await _client.dio.post('/orders', data: payload);
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw OrderApiException(ApiClient.errorMessage(e));
    }
  }

  /// GET /delivery-zones -> active delivery zones (any authenticated user).
  Future<List<Map<String, dynamic>>> listZones() async {
    try {
      final res = await _client.dio.get('/delivery-zones');
      final list = res.data as List;
      return list.cast<Map<String, dynamic>>();
    } on DioException catch (e) {
      throw OrderApiException(ApiClient.errorMessage(e));
    }
  }
}

final orderApiProvider = Provider<OrderApi>((ref) {
  return OrderApi(ref.watch(apiClientProvider));
});
