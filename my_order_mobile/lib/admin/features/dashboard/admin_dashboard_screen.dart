import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_provider.dart';
import '../../../core/flavor_provider.dart';
import 'admin_providers.dart';

/// Selected tab for the admin dashboard (shared with quick actions).
final adminTabIndexProvider = StateProvider<int>((ref) => 0);

/// Admin web dashboard — modern, responsive layout.
class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final tab = ref.watch(adminTabIndexProvider);
    final isNarrow = MediaQuery.of(context).size.width < 900;

    return Scaffold(
      backgroundColor: const Color(0xFFF3F5F9),
      body: Row(
        children: [
          if (!isNarrow)
            _Sidebar(
              selectedIndex: tab,
              onSelect: (i) =>
                  ref.read(adminTabIndexProvider.notifier).state = i,
            ),
          Expanded(
            child: Column(
              children: [
                _TopBar(
                  adminName: auth.profile?.name ?? 'Admin',
                  isNarrow: isNarrow,
                  selectedIndex: tab,
                  onNav: (i) =>
                      ref.read(adminTabIndexProvider.notifier).state = i,
                  onLogout: () => ref.read(authProvider.notifier).logout(),
                ),
                Expanded(
                  child: switch (tab) {
                    0 => const _OverviewTab(),
                    1 => const _RiderApplicationsTab(),
                    2 => const _OrderQueueTab(),
                    _ => const _OverviewTab(),
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Left navigation sidebar (desktop only).
class _Sidebar extends ConsumerWidget {
  final int selectedIndex;
  final ValueChanged<int> onSelect;
  const _Sidebar({required this.selectedIndex, required this.onSelect});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return Container(
      width: 240,
      color: const Color(0xFF111827),
      child: Column(
        children: [
          const SizedBox(height: 32),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: config.brandColor.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.local_shipping_rounded,
                    color: config.brandColor),
              ),
              const SizedBox(width: 10),
              const Text('My Order',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 19,
                      fontWeight: FontWeight.bold)),
            ],
          ),
          const Text('Admin Console',
              style: TextStyle(color: Colors.white38, fontSize: 12)),
          const SizedBox(height: 32),
          _NavItem(
            icon: Icons.dashboard_outlined,
            label: 'Overview',
            selected: selectedIndex == 0,
            onTap: () => onSelect(0),
          ),
          _NavItem(
            icon: Icons.badge_outlined,
            label: 'Rider Applications',
            selected: selectedIndex == 1,
            onTap: () => onSelect(1),
          ),
          _NavItem(
            icon: Icons.local_shipping_outlined,
            label: 'Order Queue',
            selected: selectedIndex == 2,
            onTap: () => onSelect(2),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text('Finance, disputes & settlements\narrive in Phase 5.',
                style: TextStyle(color: Colors.white24, fontSize: 11)),
          ),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _NavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFF1F2937) : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Icon(icon,
                  size: 20,
                  color: selected ? Colors.white : Colors.white54),
              const SizedBox(width: 12),
              Text(label,
                  style: TextStyle(
                      color: selected ? Colors.white : Colors.white70,
                      fontSize: 14,
                      fontWeight:
                          selected ? FontWeight.w600 : FontWeight.normal)),
            ],
          ),
        ),
      ),
    );
  }
}

/// Top bar — desktop shows inline identity; narrow shows a menu.
class _TopBar extends ConsumerWidget {
  final String adminName;
  final bool isNarrow;
  final int selectedIndex;
  final ValueChanged<int> onNav;
  final VoidCallback onLogout;
  const _TopBar({
    required this.adminName,
    required this.isNarrow,
    required this.selectedIndex,
    required this.onNav,
    required this.onLogout,
  });

  static const _labels = ['Overview', 'Rider Applications', 'Order Queue'];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              offset: const Offset(0, 2),
              blurRadius: 8),
        ],
      ),
      child: Row(
        children: [
          if (isNarrow) ...[
            Icon(Icons.local_shipping_rounded, color: const Color(0xFF1A73E8)),
            const SizedBox(width: 8),
            const Text('My Order Admin',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const Spacer(),
            PopupMenuButton<int>(
              tooltip: 'Navigate',
              icon: const Icon(Icons.menu_rounded),
              onSelected: onNav,
              itemBuilder: (_) => [
                for (var i = 0; i < _labels.length; i++)
                  PopupMenuItem(
                    value: i,
                    child: Row(
                      children: [
                        Icon(
                            i == selectedIndex
                                ? Icons.check_circle
                                : Icons.circle_outlined,
                            size: 18,
                            color: i == selectedIndex
                                ? const Color(0xFF1A73E8)
                                : Colors.grey),
                        const SizedBox(width: 10),
                        Text(_labels[i]),
                      ],
                    ),
                  ),
              ],
            ),
          ] else
            Text('Operations Dashboard',
                style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey[800])),
          const Spacer(),
          if (!isNarrow) ...[
            CircleAvatar(
              radius: 15,
              backgroundColor: const Color(0xFF111827),
              child: Text(adminName.characters.first.toUpperCase(),
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.bold)),
            ),
            const SizedBox(width: 8),
            Text(adminName,
                style: TextStyle(color: Colors.grey[700], fontSize: 14)),
            const SizedBox(width: 8),
          ],
          IconButton(
            tooltip: 'Logout',
            onPressed: onLogout,
            icon: const Icon(Icons.logout, size: 20),
            color: Colors.grey[700],
          ),
        ],
      ),
    );
  }
}

// ===========================================================================
// Overview
// ===========================================================================

class _OverviewTab extends ConsumerWidget {
  const _OverviewTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dash = ref.watch(adminDashboardProvider);

    final stats = [
      _StatData(
        icon: Icons.badge_outlined,
        label: 'Rider Applications',
        value: '${dash.riderApplications.length}',
        color: const Color(0xFFF59E0B),
        iconBg: const Color(0xFFFFF3E0),
      ),
      _StatData(
        icon: Icons.local_shipping_outlined,
        label: 'Pending Orders',
        value: '${dash.pendingOrders.length}',
        color: const Color(0xFF3B82F6),
        iconBg: const Color(0xFFE8F0FE),
      ),
      _StatData(
        icon: Icons.two_wheeler,
        label: 'Active Riders',
        value: '${dash.activeRiders.length}',
        color: const Color(0xFF10B981),
        iconBg: const Color(0xFFE7F8F1),
      ),
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Welcome back',
              style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey[900])),
          const SizedBox(height: 4),
          Text("Here's what needs your attention today.",
              style: TextStyle(color: Colors.grey[600], fontSize: 14)),
          const SizedBox(height: 24),
          // Stat cards — wrap on narrow screens.
          LayoutBuilder(builder: (context, constraints) {
            final spacing = 16.0;
            final perCard =
                (constraints.maxWidth - (spacing * (stats.length - 1))) /
                    stats.length;
            if (perCard >= 190) {
              return Row(
                children: [
                  for (var i = 0; i < stats.length; i++) ...[
                    if (i > 0) const SizedBox(width: 16),
                    Expanded(child: _StatCard(data: stats[i])),
                  ],
                ],
              );
            }
            return Column(
              children: [
                for (var i = 0; i < stats.length; i++) ...[
                  if (i > 0) const SizedBox(height: 16),
                  _StatCard(data: stats[i]),
                ],
              ],
            );
          }),
          const SizedBox(height: 24),
          Text('Quick Actions',
              style: TextStyle(
                  fontSize: 17, fontWeight: FontWeight.bold, color: Colors.grey[800])),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              _QuickAction(
                icon: Icons.badge_outlined,
                label: 'Review rider\napplications',
                color: const Color(0xFFF59E0B),
                onTap: () => ref.read(adminTabIndexProvider.notifier).state = 1,
              ),
              _QuickAction(
                icon: Icons.local_shipping_outlined,
                label: 'Assign pending\norders',
                color: const Color(0xFF3B82F6),
                onTap: () => ref.read(adminTabIndexProvider.notifier).state = 2,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatData {
  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final Color iconBg;
  const _StatData({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    required this.iconBg,
  });
}

class _StatCard extends StatelessWidget {
  final _StatData data;
  const _StatCard({required this.data});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              offset: const Offset(0, 2),
              blurRadius: 8),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
                color: data.iconBg, borderRadius: BorderRadius.circular(14)),
            child: Icon(data.icon, color: data.color, size: 28),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(data.value,
                  style: const TextStyle(
                      fontSize: 28, fontWeight: FontWeight.bold)),
              Text(data.label,
                  style: TextStyle(fontSize: 13, color: Colors.grey[600])),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: 150,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withValues(alpha: 0.3)),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withValues(alpha: 0.03),
                offset: const Offset(0, 2),
                blurRadius: 6),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 26),
            const SizedBox(height: 10),
            Text(label,
                style: const TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600, height: 1.25)),
          ],
        ),
      ),
    );
  }
}

// ===========================================================================
// Shared list card
// ===========================================================================

class _ResponsiveListCard extends ConsumerWidget {
  final String title;
  final Widget Function(bool isWide) builder;
  const _ResponsiveListCard({required this.title, required this.builder});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return LayoutBuilder(builder: (context, constraints) {
      final isWide = constraints.maxWidth >= 720;
      return Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withValues(alpha: 0.04),
                offset: const Offset(0, 2),
                blurRadius: 8),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Expanded(
                    child: Text(title,
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700)),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: () =>
                        ref.read(adminDashboardProvider.notifier).refresh(),
                    icon: const Icon(Icons.refresh, size: 20),
                    color: Colors.grey[600],
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            builder(isWide),
          ],
        ),
      );
    });
  }
}

// ===========================================================================
// Rider Applications tab
// ===========================================================================

class _RiderApplicationsTab extends ConsumerWidget {
  const _RiderApplicationsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dash = ref.watch(adminDashboardProvider);
    if (dash.loading) return const Center(child: CircularProgressIndicator());
    if (dash.error != null) return _AdminError(message: dash.error!);

    final apps = dash.riderApplications;
    if (apps.isEmpty) {
      return const _EmptyList(
          icon: Icons.verified_outlined, message: 'No pending rider applications 🎉');
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: _ResponsiveListCard(
        title: 'Pending Applications (${apps.length})',
        builder: (isWide) => isWide
            ? _ApplicationsTable(apps: apps)
            : _ApplicationsCards(apps: apps),
      ),
    );
  }
}

class _ApplicationsTable extends ConsumerWidget {
  final List<RiderApplicationItem> apps;
  const _ApplicationsTable({required this.apps});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: WidgetStatePropertyAll(const Color(0xFFF8FAFC)),
        columns: const [
          DataColumn(label: Text('NRC')),
          DataColumn(label: Text('License')),
          DataColumn(label: Text('Vehicle')),
          DataColumn(label: Text('')),
        ],
        rows: apps
            .map((a) => DataRow(cells: [
                  DataCell(Text(a.nrc)),
                  DataCell(Text(a.licenseNumber)),
                  DataCell(Text(a.vehiclePlate)),
                  DataCell(Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _RejectButton(
                          onPressed: () => ref
                              .read(adminDashboardProvider.notifier)
                              .rejectApplication(a.id)),
                      const SizedBox(width: 8),
                      _ApproveButton(
                          onPressed: () => ref
                              .read(adminDashboardProvider.notifier)
                              .approveApplication(a.id)),
                    ],
                  )),
                ]))
            .toList(),
      ),
    );
  }
}

class _ApplicationsCards extends ConsumerWidget {
  final List<RiderApplicationItem> apps;
  const _ApplicationsCards({required this.apps});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          for (final a in apps)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _ApplicationCard(app: a),
            ),
        ],
      ),
    );
  }
}

class _ApplicationCard extends ConsumerWidget {
  final RiderApplicationItem app;
  const _ApplicationCard({required this.app});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFAFBFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _LabeledValue(label: 'NRC', value: app.nrc),
          _LabeledValue(label: 'License', value: app.licenseNumber),
          _LabeledValue(label: 'Vehicle', value: app.vehiclePlate),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              _RejectButton(
                  onPressed: () => ref
                      .read(adminDashboardProvider.notifier)
                      .rejectApplication(app.id)),
              const SizedBox(width: 8),
              _ApproveButton(
                  onPressed: () => ref
                      .read(adminDashboardProvider.notifier)
                      .approveApplication(app.id)),
            ],
          ),
        ],
      ),
    );
  }
}

// ===========================================================================
// Order Queue tab
// ===========================================================================

class _OrderQueueTab extends ConsumerWidget {
  const _OrderQueueTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dash = ref.watch(adminDashboardProvider);
    if (dash.loading) return const Center(child: CircularProgressIndicator());
    if (dash.error != null) return _AdminError(message: dash.error!);

    final orders = dash.pendingOrders;
    if (orders.isEmpty) {
      return const _EmptyList(
          icon: Icons.done_all, message: 'No pending orders 🎉');
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: _ResponsiveListCard(
        title: 'Pending Orders (${orders.length})',
        builder: (isWide) => isWide
            ? _OrdersTable(orders: orders)
            : _OrdersCards(orders: orders),
      ),
    );
  }
}

class _OrdersTable extends ConsumerWidget {
  final List<AdminOrderItem> orders;
  const _OrdersTable({required this.orders});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: WidgetStatePropertyAll(const Color(0xFFF8FAFC)),
        columns: const [
          DataColumn(label: Text('Recipient')),
          DataColumn(label: Text('Pickup')),
          DataColumn(label: Text('Dropoff')),
          DataColumn(label: Text('Fee')),
          DataColumn(label: Text('')),
        ],
        rows: orders
            .map((o) => DataRow(cells: [
                  DataCell(Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(o.recipientName,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text(o.recipientPhone,
                          style: TextStyle(
                              fontSize: 12, color: Colors.grey[600])),
                    ],
                  )),
                  DataCell(SizedBox(
                      width: 140,
                      child: Text(o.pickupAddress,
                          overflow: TextOverflow.ellipsis))),
                  DataCell(SizedBox(
                      width: 140,
                      child: Text(o.dropoffAddress,
                          overflow: TextOverflow.ellipsis))),
                  DataCell(Text('${o.fee} MMK')),
                  DataCell(_AssignButton(
                    order: o,
                    enabled: ref.watch(adminDashboardProvider).activeRiders.isNotEmpty,
                  )),
                ]))
            .toList(),
      ),
    );
  }
}

class _OrdersCards extends ConsumerWidget {
  final List<AdminOrderItem> orders;
  const _OrdersCards({required this.orders});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          for (final o in orders)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _OrderCard(order: o),
            ),
        ],
      ),
    );
  }
}

class _OrderCard extends ConsumerWidget {
  final AdminOrderItem order;
  const _OrderCard({required this.order});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFAFBFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(order.isWalkin
                  ? Icons.storefront_outlined
                  : Icons.send_outlined,
                  size: 20,
                  color: Colors.grey[600]),
              const SizedBox(width: 8),
              Expanded(
                child: Text('${order.recipientName}',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
              Text('${order.fee} MMK',
                  style: TextStyle(
                      fontWeight: FontWeight.bold, color: Colors.grey[800])),
            ],
          ),
          Text(order.recipientPhone,
              style: TextStyle(fontSize: 12, color: Colors.grey[500])),
          const SizedBox(height: 8),
          _LabeledValue(label: 'Pickup', value: order.pickupAddress),
          _LabeledValue(label: 'Dropoff', value: order.dropoffAddress),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: _AssignButton(
              order: order,
              enabled: ref.watch(adminDashboardProvider).activeRiders.isNotEmpty,
            ),
          ),
        ],
      ),
    );
  }
}

// ===========================================================================
// Shared buttons & bits
// ===========================================================================

class _ApproveButton extends StatelessWidget {
  final VoidCallback onPressed;
  const _ApproveButton({required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return FilledButton(
      style: FilledButton.styleFrom(
        backgroundColor: const Color(0xFF10B981),
        padding: const EdgeInsets.symmetric(horizontal: 16),
      ),
      onPressed: onPressed,
      child: const Text('Approve'),
    );
  }
}

class _RejectButton extends StatelessWidget {
  final VoidCallback onPressed;
  const _RejectButton({required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      style: OutlinedButton.styleFrom(
        foregroundColor: const Color(0xFFEF4444),
        side: const BorderSide(color: Color(0xFFFECACA)),
        padding: const EdgeInsets.symmetric(horizontal: 16),
      ),
      onPressed: onPressed,
      child: const Text('Reject'),
    );
  }
}

class _AssignButton extends ConsumerWidget {
  final AdminOrderItem order;
  final bool enabled;
  const _AssignButton({required this.order, required this.enabled});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FilledButton(
      style: FilledButton.styleFrom(
        backgroundColor: const Color(0xFF1A73E8),
        padding: const EdgeInsets.symmetric(horizontal: 18),
      ),
      onPressed: enabled
          ? () => _showAssignDialog(context, ref, order)
          : null,
      child: const Text('Assign'),
    );
  }

  Future<void> _showAssignDialog(
      BuildContext context, WidgetRef ref, AdminOrderItem order) async {
    final dash = ref.read(adminDashboardProvider);
    String? selected =
        dash.activeRiders.isNotEmpty ? dash.activeRiders.first.userId : null;

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Assign Rider'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Order to ${order.recipientName} (${order.recipientPhone})',
                style: TextStyle(color: Colors.grey[600], fontSize: 13)),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: selected,
              decoration: const InputDecoration(labelText: 'Select rider'),
              items: dash.activeRiders
                  .map((r) => DropdownMenuItem(
                      value: r.userId, child: Text('${r.name} (${r.phone})')))
                  .toList(),
              onChanged: (v) => selected = v,
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              if (selected != null) {
                ref.read(adminDashboardProvider.notifier).assignOrder(order.id, selected!);
              }
            },
            child: const Text('Assign'),
          ),
        ],
      ),
    );
  }
}

class _EmptyList extends StatelessWidget {
  final IconData icon;
  final String message;
  const _EmptyList({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(48),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: const Color(0xFF10B981)),
            const SizedBox(height: 12),
            Text(message,
                style: TextStyle(color: Colors.grey[600], fontSize: 16)),
          ],
        ),
      ),
    );
  }
}

class _AdminError extends ConsumerWidget {
  final String message;
  const _AdminError({required this.message});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded,
                size: 52, color: Colors.red.shade400),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () =>
                  ref.read(adminDashboardProvider.notifier).refresh(),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _LabeledValue extends StatelessWidget {
  final String label;
  final String value;
  const _LabeledValue({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 60,
            child: Text(label,
                style: TextStyle(fontSize: 12, color: Colors.grey[500])),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}
