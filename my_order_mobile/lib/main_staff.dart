import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/app_config.dart';
import 'core/flavor_provider.dart';
import 'core/widgets/shared_auth_scaffold.dart';
import 'staff/features/home/staff_home_screen.dart';

void main() {
  runApp(
    ProviderScope(
      overrides: [
        flavorProvider.overrideWithValue(FlavorConfig.staff),
      ],
      child: const _StaffApp(),
    ),
  );
}

class _StaffApp extends ConsumerWidget {
  const _StaffApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return FlavorApp(
      config: config,
      homeBuilder: (context) => const StaffHomeScreen(),
    );
  }
}
