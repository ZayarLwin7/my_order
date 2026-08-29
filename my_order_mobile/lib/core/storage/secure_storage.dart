import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// JWT token storage backed by flutter_secure_storage.
class TokenStorage {
  static const _key = 'my_order_access_token';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<String?> read() => _storage.read(key: _key);

  Future<void> write(String token) => _storage.write(key: _key, value: token);

  Future<void> clear() => _storage.delete(key: _key);
}

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());
