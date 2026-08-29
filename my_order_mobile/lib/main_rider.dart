import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/app_config.dart';
import 'core/flavor_provider.dart';
import 'core/widgets/shared_auth_scaffold.dart';
import 'rider/features/home/rider_home_screen.dart';

void main() {
  runApp(
    ProviderScope(
      overrides: [
        flavorProvider.overrideWithValue(FlavorConfig.rider),
      ],
      child: const _RiderApp(),
    ),
  );
}

class _RiderApp extends ConsumerWidget {
  const _RiderApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return FlavorApp(
      config: config,
      homeBuilder: (context) => const RiderHomeScreen(),
    );
  }
}
