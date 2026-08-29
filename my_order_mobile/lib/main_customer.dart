import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/app_config.dart';
import 'core/flavor_provider.dart';
import 'core/widgets/shared_auth_scaffold.dart';
import 'customer/features/home/customer_home_screen.dart';

void main() {
  runApp(
    ProviderScope(
      overrides: [
        flavorProvider.overrideWithValue(FlavorConfig.customer),
      ],
      child: const _CustomerApp(),
    ),
  );
}

class _CustomerApp extends ConsumerWidget {
  const _CustomerApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return FlavorApp(
      config: config,
      homeBuilder: (context) => const CustomerHomeScreen(),
    );
  }
}
