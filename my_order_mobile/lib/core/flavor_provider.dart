import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app_config.dart';

/// Set at app startup by each flavor's main_*.dart entrypoint.
final flavorProvider = Provider<FlavorConfig>((ref) {
  throw UnimplementedError('flavorProvider must be overridden in main_*.dart');
});
