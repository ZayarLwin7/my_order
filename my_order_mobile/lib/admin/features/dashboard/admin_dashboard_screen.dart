import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_provider.dart';
import '../../../core/flavor_provider.dart';
import 'admin_providers.dart';

/// Selected tab for the admin dashboard (shared with quick actions).
final adminTabIndexProvider = StateProvider<int>((ref) => 0);

/// Modern admin design tokens.
class AdminDesign {
  AdminDesign._();

  static const sidebarTop = Color(0xFF1B1B3A);
  static const sidebarBottom = Color(0xFF0A0E1F);
  static const sidebarText = Color(0xFFE8EAF6);
  static const sidebarMuted = Color(0xFF8A8FB8);

  static const canvas = Color(0xFFF5F6FA);
  static const surface = Colors.white;
  static const border = Color(0xFFE7E9F2);
  static const ink = Color(0xFF161A2B);
  static const inkSoft = Color(0xFF6B7194);

  static const indigo = Color(0xFF4F46E5);
  static const indigoSoft = Color(0xFFEEF0FF);
  static const emerald = Color(0xFF10B981);
  static const emeraldSoft = Color(0xFFE7F8F1);
  static const amber = Color(0xFFF59E0B);
  static const amberSoft = Color(0xFFFFF3E0);
  static const blue = Color(0xFF3B82F6);
  static const blueSoft = Color(0xFFE8F0FE);
  static const rose = Color(0xFFEF4444);
  static const roseSoft = Color(0xFFFEECEC);
  static const violet = Color(0xFF8B5CF6);
  static const violetSoft = Color(0xFFF3EEFF);

  static List<BoxShadow> soft([double s = 1]) => [
        BoxShadow(
          color: const Color(0x141A2B5E).withValues(alpha: 0.07 * s),
          offset: const Offset(0, 8),
          blurRadius: 22,
          spreadRadius: 0,
        ),
        BoxShadow(
          color: const Color(0x141A2B5E).withValues(alpha: 0.04 * s),
          offset: const Offset(0, 2),
          blurRadius: 6,
          spreadRadius: 0,
        ),
      ];

  static const radius = 20.0;
}

/// Admin web dashboard — high-fidelity operations console.
class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final tab = ref.watch(adminTabIndexProvider);
    final isNarrow = MediaQuery.of(context).size.width < 980;

    return Scaffold(
      backgroundColor: AdminDesign.canvas,
      body: Row(
        children: [
          if (!isNarrow)
            _Sidebar(
              selectedIndex: tab,
              onSelect: (i) => ref.read(adminTabIndexProvider.notifier).state = i,
            ),
          Expanded(
            child: Column(
              children: [
                _TopBar(
                  adminName: auth.profile?.name ?? 'Admin',
                  isNarrow: isNarrow,
                  selectedIndex: tab,
                  onNav: (i) => ref.read(adminTabIndexProvider.notifier).state = i,
                  onLogout: () => ref.read(authProvider.notifier).logout(),
                ),
                Expanded(
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 260),
                    switchInCurve: Curves.easeOutCubic,
                    switchOutCurve: Curves.easeInCubic,
                    transitionBuilder: (child, anim) => FadeTransition(
                      opacity: anim,
                      child: SlideTransition(
                        position: Tween<Offset>(
                          begin: const Offset(0, 0.03),
                          end: Offset.zero,
                        ).animate(anim),
                        child: child,
                      ),
                    ),
                    child: KeyedSubtree(
                      key: ValueKey(tab),
                      child: switch (tab) {
                        0 => const _OverviewTab(),
                        1 => const _RiderApplicationsTab(),
                        2 => const _OrderQueueTab(),
                        _ => const _OverviewTab(),
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Left navigation sidebar (desktop).
class _Sidebar extends ConsumerWidget {
  final int selectedIndex;
  final ValueChanged<int> onSelect;
  const _Sidebar({required this.selectedIndex, required this.onSelect});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    final dash = ref.watch(adminDashboardProvider);
    return Container(
      width: 256,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [AdminDesign.sidebarTop, AdminDesign.sidebarBottom],
        ),
      ),
      child: Column(
        children: [
          const SizedBox(height: 24),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: config.brandColor.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: config.brandColor.withValues(alpha: 0.35),
                        blurRadius: 14,
                      ),
                    ],
                  ),
                  child: Icon(Icons.local_shipping_rounded,
                      color: config.brandColor, size: 22),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('My Order',
                          style: TextStyle(
                              color: AdminDesign.sidebarText,
                              fontSize: 18,
                              fontWeight: FontWeight.bold)),
                      Text('Admin Console',
                          style: TextStyle(
                              color: AdminDesign.sidebarMuted, fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 26),
          const _SectionLabel('Operations'),
          _NavItem(
            icon: Icons.dashboard_outlined,
            label: 'Overview',
            selected: selectedIndex == 0,
            onTap: () => onSelect(0),
          ),
          _NavItem(
            icon: Icons.badge_outlined,
            label: 'Rider Applications',
            badge: dash.riderApplications.length,
            selected: selectedIndex == 1,
            onTap: () => onSelect(1),
          ),
          _NavItem(
            icon: Icons.local_shipping_outlined,
            label: 'Order Queue',
            badge: dash.pendingOrders.length,
            selected: selectedIndex == 2,
            onTap: () => onSelect(2),
          ),
          const SizedBox(height: 14),
          const _SectionLabel('Coming Soon'),
          _NavItem(
            icon: Icons.account_balance_wallet_outlined,
            label: 'Finance',
            muted: true,
            onTap: () {},
          ),
          _NavItem(
            icon: Icons.gpp_maybe_outlined,
            label: 'Disputes',
            muted: true,
            onTap: () {},
          ),
          const Spacer(),
          _SidebarUser(
              name: ref.watch(authProvider).profile?.name ?? 'Admin'),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(left: 28, right: 14, top: 10, bottom: 6),
        child: Text(text.toUpperCase(),
            style: const TextStyle(
                color: AdminDesign.sidebarMuted,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.2)),
      );
}

class _NavItem extends StatefulWidget {
  final IconData icon;
  final String label;
  final int? badge;
  final bool selected;
  final bool muted;
  final VoidCallback onTap;
  const _NavItem({
    required this.icon,
    required this.label,
    this.badge,
    this.selected = false,
    this.muted = false,
    required this.onTap,
  });

  @override
  State<_NavItem> createState() => _NavItemState();
}

class _NavItemState extends State<_NavItem> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final active = widget.selected && !widget.muted;
    final interactive = !widget.muted;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 3),
      child: MouseRegion(
        onEnter: (_) => setState(() => _hover = true),
        onExit: (_) => setState(() => _hover = false),
        child: InkWell(
          onTap: interactive ? widget.onTap : null,
          borderRadius: BorderRadius.circular(12),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            decoration: BoxDecoration(
              color: active
                  ? AdminDesign.indigo
                  : (_hover && interactive
                      ? Colors.white.withValues(alpha: 0.06)
                      : Colors.transparent),
              borderRadius: BorderRadius.circular(12),
              boxShadow: active
                  ? [
                      BoxShadow(
                        color: AdminDesign.indigo.withValues(alpha: 0.45),
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : null,
            ),
            child: Row(
              children: [
                if (active)
                  Container(
                    width: 3,
                    height: 18,
                    margin: const EdgeInsets.only(right: 10),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  )
                else
                  const SizedBox(width: 13),
                Icon(widget.icon,
                    size: 19,
                    color: active
                        ? Colors.white
                        : (widget.muted
                            ? AdminDesign.sidebarMuted.withValues(alpha: 0.6)
                            : (_hover
                                ? AdminDesign.sidebarText
                                : AdminDesign.sidebarMuted))),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(widget.label,
                      style: TextStyle(
                        color: active
                            ? Colors.white
                            : (widget.muted
                                ? AdminDesign.sidebarMuted.withValues(alpha: 0.6)
                                : (_hover
                                    ? AdminDesign.sidebarText
                                    : AdminDesign.sidebarMuted)),
                        fontSize: 13.5,
                        fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                      )),
                ),
                if (widget.badge != null && widget.badge! > 0)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: active
                          ? Colors.white.withValues(alpha: 0.22)
                          : AdminDesign.amber.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text('${widget.badge}',
                        style: TextStyle(
                            color: active ? Colors.white : AdminDesign.amber,
                            fontSize: 11,
                            fontWeight: FontWeight.w700)),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SidebarUser extends StatelessWidget {
  final String name;
  const _SidebarUser({required this.name});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(2.5),
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                      colors: [AdminDesign.indigo, AdminDesign.blue]),
                  borderRadius: BorderRadius.all(Radius.circular(20)),
                ),
                child: CircleAvatar(
                  radius: 14,
                  backgroundColor: AdminDesign.sidebarBottom,
                  child: Text(name.characters.first.toUpperCase(),
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name,
                        style: const TextStyle(
                            color: AdminDesign.sidebarText,
                            fontSize: 13,
                            fontWeight: FontWeight.w600)),
                    const Text('Administrator',
                        style: TextStyle(
                            color: AdminDesign.sidebarMuted, fontSize: 11)),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
}

/// Top bar.
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

  static const _titles = ['Overview', 'Rider Applications', 'Order Queue'];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      height: 66,
      padding: const EdgeInsets.symmetric(horizontal: 22),
      decoration: BoxDecoration(
        color: AdminDesign.surface,
        border: const Border(bottom: BorderSide(color: AdminDesign.border)),
        boxShadow: AdminDesign.soft(0.5),
      ),
      child: Row(
        children: [
          if (isNarrow) ...[
            const Icon(Icons.local_shipping_rounded, color: AdminDesign.indigo),
            const SizedBox(width: 8),
            Text('My Order Admin',
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 16)),
            const Spacer(),
            PopupMenuButton<int>(
              tooltip: 'Navigate',
              icon: const Icon(Icons.menu_rounded),
              onSelected: onNav,
              itemBuilder: (_) => [
                for (var i = 0; i < _titles.length; i++)
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
                                ? AdminDesign.indigo
                                : Colors.grey),
                        const SizedBox(width: 10),
                        Text(_titles[i]),
                      ],
                    ),
                  ),
              ],
            ),
          ] else ...[
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(_titles[selectedIndex],
                    style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AdminDesign.ink)),
                const Text('Operations',
                    style: TextStyle(
                        fontSize: 12, color: AdminDesign.inkSoft)),
              ],
            ),
            const Spacer(),
            Container(
              width: 280,
              height: 40,
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: AdminDesign.canvas,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AdminDesign.border),
              ),
              child: const Row(
                children: [
                  Icon(Icons.search, size: 18, color: AdminDesign.inkSoft),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text('Search orders, riders, applications\u2026',
                        style: TextStyle(
                            fontSize: 13, color: AdminDesign.inkSoft)),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 24),
            Container(
              padding: const EdgeInsets.all(9),
              decoration: BoxDecoration(
                color: AdminDesign.indigoSoft,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.notifications_none_rounded,
                  size: 19, color: AdminDesign.indigo),
            ),
            const SizedBox(width: 16),
            Container(
              padding: const EdgeInsets.all(2.5),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                    colors: [AdminDesign.indigo, AdminDesign.blue]),
                borderRadius: BorderRadius.all(Radius.circular(20)),
              ),
              child: CircleAvatar(
                radius: 15,
                backgroundColor: AdminDesign.sidebarBottom,
                child: Text(adminName.characters.first.toUpperCase(),
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(width: 10),
            Text(adminName,
                style: const TextStyle(
                    color: AdminDesign.ink,
                    fontSize: 14,
                    fontWeight: FontWeight.w600)),
            const SizedBox(width: 8),
            IconButton(
              tooltip: 'Logout',
              onPressed: onLogout,
              icon: const Icon(Icons.logout, size: 19),
              color: AdminDesign.inkSoft,
            ),
          ],
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
    final apps = dash.riderApplications;
    final orders = dash.pendingOrders;

    final kpis = [
      _Kpi(
        label: 'Rider Applications',
        value: apps.length,
        unit: 'new',
        color: AdminDesign.amber,
        soft: AdminDesign.amberSoft,
        icon: Icons.badge_outlined,
        trendPct: 12.5,
        seed: 3,
        caption: 'Awaiting review',
      ),
      _Kpi(
        label: 'Pending Orders',
        value: orders.length,
        unit: 'open',
        color: AdminDesign.blue,
        soft: AdminDesign.blueSoft,
        icon: Icons.local_shipping_outlined,
        trendPct: 6.2,
        seed: 7,
        caption: 'Ready to assign',
      ),
      _Kpi(
        label: 'Active Riders',
        value: dash.activeRiders.length,
        unit: 'live',
        color: AdminDesign.emerald,
        soft: AdminDesign.emeraldSoft,
        icon: Icons.two_wheeler,
        trendPct: 3.1,
        seed: 11,
        caption: 'On the road',
      ),
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Good day, ${ref.watch(authProvider).profile?.name ?? 'Admin'} 👋',
              style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AdminDesign.ink)),
          const SizedBox(height: 4),
          Text("Here's what needs your attention today.",
              style: TextStyle(color: AdminDesign.inkSoft, fontSize: 14)),
          const SizedBox(height: 24),
          LayoutBuilder(builder: (c, constraints) {
            final gap = 18.0;
            final per = (constraints.maxWidth - gap * (kpis.length - 1)) / kpis.length;
            if (per >= 220) {
              return Row(
                children: [
                  for (var i = 0; i < kpis.length; i++) ...[
                    if (i > 0) SizedBox(width: gap),
                    Expanded(child: _KpiCard(kpi: kpis[i])),
                  ],
                ],
              );
            }
            return Column(
              children: [
                for (var i = 0; i < kpis.length; i++) ...[
                  if (i > 0) SizedBox(height: gap),
                  _KpiCard(kpi: kpis[i]),
                ],
              ],
            );
          }),
          const SizedBox(height: 24),
          LayoutBuilder(builder: (c, constraints) {
            final twoCol = constraints.maxWidth >= 820;
            return twoCol
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                          flex: 3,
                          child: _AttentionPanel(
                              apps: apps, orders: orders)),
                      const SizedBox(width: 18),
                      Expanded(
                        flex: 2,
                        child: Column(
                          children: const [
                            _QuickActionsPanel(),
                            SizedBox(height: 18),
                            _ActivityPanel(),
                          ],
                        ),
                      ),
                    ],
                  )
                : Column(
                    children: [
                      _AttentionPanel(apps: apps, orders: orders),
                      const SizedBox(height: 18),
                      const _QuickActionsPanel(),
                      const SizedBox(height: 18),
                      const _ActivityPanel(),
                    ],
                  );
          }),
        ],
      ),
    );
  }
}

class _Kpi {
  final String label;
  final int value;
  final String unit;
  final Color color;
  final Color soft;
  final IconData icon;
  final double trendPct;
  final int seed;
  final String caption;
  const _Kpi({
    required this.label,
    required this.value,
    required this.unit,
    required this.color,
    required this.soft,
    required this.icon,
    required this.trendPct,
    required this.seed,
    required this.caption,
  });
}

class _KpiCard extends StatefulWidget {
  final _Kpi kpi;
  const _KpiCard({required this.kpi});
  @override
  State<_KpiCard> createState() => _KpiCardState();
}

class _KpiCardState extends State<_KpiCard> {
  bool _hover = false;
  @override
  Widget build(BuildContext context) {
    final k = widget.kpi;
    final trendUp = k.trendPct >= 0;
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: AdminDesign.surface,
          borderRadius: BorderRadius.circular(AdminDesign.radius),
          border: Border.all(color: AdminDesign.border),
          boxShadow: AdminDesign.soft(_hover ? 1.4 : 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.all(11),
                  decoration: BoxDecoration(
                    color: k.soft,
                    borderRadius: BorderRadius.circular(13),
                  ),
                  child: Icon(k.icon, color: k.color, size: 22),
                ),
                _Sparkline(
                  color: k.color,
                  seed: k.seed,
                  value: k.value,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text('${k.value}',
                    style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        fontFeatures: [FontFeature.tabularFigures()],
                        color: AdminDesign.ink)),
                const SizedBox(width: 8),
                Text(k.unit,
                    style: TextStyle(
                        fontSize: 13, color: AdminDesign.inkSoft)),
              ],
            ),
            const SizedBox(height: 4),
            Text(k.label,
                style: const TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    color: AdminDesign.ink)),
            const SizedBox(height: 10),
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: (trendUp ? AdminDesign.emerald : AdminDesign.rose)
                        .withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                          trendUp
                              ? Icons.trending_up_rounded
                              : Icons.trending_down_rounded,
                          size: 13,
                          color: trendUp
                              ? AdminDesign.emerald
                              : AdminDesign.rose),
                      const SizedBox(width: 3),
                      Text('${trendUp ? '+' : ''}${k.trendPct.toStringAsFixed(1)}%',
                          style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: trendUp
                                  ? AdminDesign.emerald
                                  : AdminDesign.rose)),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Text(k.caption,
                    style: TextStyle(
                        fontSize: 11.5, color: AdminDesign.inkSoft)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Tiny deterministic sparkline so cards feel alive without fake backend data.
class _Sparkline extends StatelessWidget {
  final Color color;
  final int seed;
  final int value;
  const _Sparkline(
      {required this.color, required this.seed, required this.value});

  @override
  Widget build(BuildContext context) {
    final rnd = math.Random(seed * 7919 + 13);
    const n = 12;
    final pts = List<double>.generate(n, (i) {
      final base = 0.5 + 0.32 * math.sin(i / 1.7 + seed);
      final noise = (rnd.nextDouble() - 0.5) * 0.25;
      return (base + noise).clamp(0.08, 0.95);
    });
    final w = 78.0, h = 34.0;
    return CustomPaint(
      size: Size(w, h),
      painter: _SparkPainter(pts, color),
    );
  }
}

class _SparkPainter extends CustomPainter {
  final List<double> pts;
  final Color color;
  _SparkPainter(this.pts, this.color);
  @override
  void paint(Canvas canvas, Size size) {
    final n = pts.length;
    final step = size.width / (n - 1);
    final path = Path();
    final fill = Path();
    for (var i = 0; i < n; i++) {
      final x = i * step;
      final y = size.height - pts[i] * size.height;
      if (i == 0) {
        path.moveTo(x, y);
        fill.moveTo(x, size.height);
        fill.lineTo(x, y);
      } else {
        path.lineTo(x, y);
        fill.lineTo(x, y);
      }
    }
    fill.lineTo(size.width, size.height);
    fill.close();
    final fillPaint = Paint()
      ..color = color.withValues(alpha: 0.12)
      ..style = PaintingStyle.fill;
    canvas.drawPath(fill, fillPaint);
    final line = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(path, line);
    final last = pts.last;
    canvas.drawCircle(
        Offset(size.width, size.height - last * size.height), 3, line);
  }

  @override
  bool shouldRepaint(covariant _SparkPainter old) =>
      old.pts != pts || old.color != color;
}

class _AttentionPanel extends StatelessWidget {
  final List<RiderApplicationItem> apps;
  final List<AdminOrderItem> orders;
  const _AttentionPanel({required this.apps, required this.orders});

  @override
  Widget build(BuildContext context) {
    final items = <_AttentionRow>[];
    for (final a in apps) {
      items.add(_AttentionRow(
        color: AdminDesign.amber,
        soft: AdminDesign.amberSoft,
        icon: Icons.badge_outlined,
        title: 'Rider application',
        subtitle: '${a.nrc} · ${a.vehiclePlate}',
        tag: 'Pending',
      ));
    }
    for (final o in orders) {
      items.add(_AttentionRow(
        color: AdminDesign.blue,
        soft: AdminDesign.blueSoft,
        icon: o.isWalkin ? Icons.storefront_outlined : Icons.send_outlined,
        title: 'Order to ${o.recipientName}',
        subtitle: o.pickupAddress,
        tag: o.isWalkin ? 'Walk-in' : 'Pickup',
      ));
    }
    return _Panel(
      title: 'Needs your attention',
      trailing: items.isEmpty ? null : '${items.length}',
      child: items.isEmpty
          ? const _EmptyHint(
              icon: Icons.celebration_outlined,
              message: 'All caught up. Nothing pending 🎉')
          : Column(
              children: [
                for (var i = 0; i < items.length; i++) ...[
                  if (i > 0)
                    Divider(height: 1, color: AdminDesign.border),
                  items[i],
                ],
              ],
            ),
    );
  }
}

class _AttentionRow extends StatelessWidget {
  final Color color;
  final Color soft;
  final IconData icon;
  final String title;
  final String subtitle;
  final String tag;
  const _AttentionRow({
    required this.color,
    required this.soft,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.tag,
  });
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 18),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(9),
              decoration: BoxDecoration(
                color: soft,
                borderRadius: BorderRadius.circular(11),
              ),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 14)),
                  const SizedBox(height: 2),
                  Text(subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                          fontSize: 12, color: AdminDesign.inkSoft)),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(tag,
                  style: TextStyle(
                      color: color,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      );
}

class _QuickActionsPanel extends StatelessWidget {
  const _QuickActionsPanel();
  @override
  Widget build(BuildContext context) => _Panel(
        title: 'Quick Actions',
        child: Consumer(builder: (c, ref, _) {
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18),
            child: Column(
              children: [
                const SizedBox(height: 18),
                _QuickTile(
                  color: AdminDesign.amber,
                  icon: Icons.badge_outlined,
                  label: 'Review rider applications',
                  onTap: () =>
                      ref.read(adminTabIndexProvider.notifier).state = 1,
                ),
                const SizedBox(height: 18),
                _QuickTile(
                  color: AdminDesign.blue,
                  icon: Icons.local_shipping_outlined,
                  label: 'Assign pending orders',
                  onTap: () =>
                      ref.read(adminTabIndexProvider.notifier).state = 2,
                ),
                const SizedBox(height: 4),
              ],
            ),
          );
        }),
      );
}

class _QuickTile extends StatefulWidget {
  final Color color;
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _QuickTile({
    required this.color,
    required this.icon,
    required this.label,
    required this.onTap,
  });
  @override
  State<_QuickTile> createState() => _QuickTileState();
}

class _QuickTileState extends State<_QuickTile> {
  bool _hover = false;
  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: InkWell(
        onTap: widget.onTap,
        borderRadius: BorderRadius.circular(14),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
          decoration: BoxDecoration(
            color: widget.color.withValues(alpha: _hover ? 0.14 : 0.08),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
                color: widget.color.withValues(alpha: _hover ? 0.7 : 0.5)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: widget.color.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(widget.icon, color: widget.color, size: 22),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(widget.label,
                    style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AdminDesign.ink)),
              ),
              Icon(Icons.arrow_forward_ios_rounded,
                  size: 16, color: widget.color),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActivityPanel extends StatelessWidget {
  const _ActivityPanel();
  @override
  Widget build(BuildContext context) => const _Panel(
        title: 'Recent Activity',
        child: Column(
          children: [
            _ActivityRow(
                color: AdminDesign.emerald,
                text: 'Rider verified item size',
                time: '2m ago'),
            Divider(height: 1, color: AdminDesign.border),
            _ActivityRow(
                color: AdminDesign.blue,
                text: 'New order created',
                time: '14m ago'),
            Divider(height: 1, color: AdminDesign.border),
            _ActivityRow(
                color: AdminDesign.amber,
                text: 'Application submitted',
                time: '1h ago'),
          ],
        ),
      );
}

class _ActivityRow extends StatelessWidget {
  final Color color;
  final String text;
  final String time;
  const _ActivityRow(
      {required this.color, required this.text, required this.time});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 11, horizontal: 18),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(text,
                  style: const TextStyle(fontSize: 13, color: AdminDesign.ink)),
            ),
            Text(time,
                style: TextStyle(fontSize: 11.5, color: AdminDesign.inkSoft)),
          ],
        ),
      );
}

class _Panel extends StatelessWidget {
  final String title;
  final String? trailing;
  final Widget child;
  const _Panel(
      {required this.title, this.trailing, required this.child});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: AdminDesign.surface,
          borderRadius: BorderRadius.circular(AdminDesign.radius),
          border: Border.all(color: AdminDesign.border),
          boxShadow: AdminDesign.soft(),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  Container(
                    width: 4,
                    height: 16,
                    margin: const EdgeInsets.only(right: 10),
                    decoration: BoxDecoration(
                      color: AdminDesign.indigo,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  Expanded(
                    child: Text(title,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w700)),
                  ),
                  if (trailing != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 9, vertical: 2),
                      decoration: BoxDecoration(
                        color: AdminDesign.indigoSoft,
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(trailing!,
                          style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: AdminDesign.indigo)),
                    ),
                ],
              ),
            ),
            const Divider(height: 1, color: AdminDesign.border),
            child,
            const SizedBox(height: 8),
          ],
        ),
      );
}

class _EmptyHint extends StatelessWidget {
  final IconData icon;
  final String message;
  const _EmptyHint({required this.icon, required this.message});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            Icon(icon, size: 40, color: AdminDesign.emerald),
            const SizedBox(height: 10),
            Text(message,
                style: TextStyle(color: AdminDesign.inkSoft, fontSize: 14)),
          ],
        ),
      );
}

// ===========================================================================
// Shared list card with search + filter
// ===========================================================================

class _ResponsiveListCard extends ConsumerWidget {
  final String title;
  final String? count;
  final Widget Function(bool isWide) builder;
  const _ResponsiveListCard({
    required this.title,
    this.count,
    required this.builder,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return LayoutBuilder(builder: (context, constraints) {
      final isWide = constraints.maxWidth >= 760;
      return Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: AdminDesign.surface,
          borderRadius: BorderRadius.circular(AdminDesign.radius),
          border: Border.all(color: AdminDesign.border),
          boxShadow: AdminDesign.soft(),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  Container(
                    width: 4,
                    height: 16,
                    margin: const EdgeInsets.only(right: 10),
                    decoration: BoxDecoration(
                      color: AdminDesign.indigo,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  Expanded(
                    child: Text(
                        count != null ? '$title ($count)' : title,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w700)),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: () => ref
                        .read(adminDashboardProvider.notifier)
                        .refresh(),
                    icon: const Icon(Icons.refresh, size: 19),
                    color: AdminDesign.inkSoft,
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: AdminDesign.border),
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
          icon: Icons.verified_outlined,
          message: 'No pending rider applications 🎉');
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: _ResponsiveListCard(
        title: 'Pending Applications',
        count: '${apps.length}',
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
      padding: const EdgeInsets.all(8),
      child: DataTable(
        headingRowColor: const WidgetStatePropertyAll(AdminDesign.indigoSoft),
        headingTextStyle: const TextStyle(
            fontWeight: FontWeight.w700, color: AdminDesign.ink, fontSize: 12),
        dataRowMinHeight: 60,
        columns: const [
          DataColumn(label: Text('Applicant')),
          DataColumn(label: Text('NRC')),
          DataColumn(label: Text('License')),
          DataColumn(label: Text('Vehicle')),
          DataColumn(label: Text('Status')),
          DataColumn(label: Text('')),
        ],
        rows: apps
            .map((a) => DataRow(cells: [
                  DataCell(_PersonCell(name: 'Rider ${a.nrc}', sub: a.submittedAt)),
                  DataCell(Text(a.nrc)),
                  DataCell(Text(a.licenseNumber)),
                  DataCell(Text(a.vehiclePlate)),
                  DataCell(_StatusChip(label: a.status)),
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
        color: AdminDesign.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AdminDesign.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _Avatar(initials: 'R'),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Rider ${app.nrc}',
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 14)),
                    Text(app.submittedAt,
                        style: TextStyle(
                            fontSize: 12, color: AdminDesign.inkSoft)),
                  ],
                ),
              ),
              _StatusChip(label: app.status),
            ],
          ),
          const SizedBox(height: 12),
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
      padding: const EdgeInsets.all(28),
      child: _ResponsiveListCard(
        title: 'Pending Orders',
        count: '${orders.length}',
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
      padding: const EdgeInsets.all(8),
      child: DataTable(
        headingRowColor: const WidgetStatePropertyAll(AdminDesign.indigoSoft),
        headingTextStyle: const TextStyle(
            fontWeight: FontWeight.w700, color: AdminDesign.ink, fontSize: 12),
        dataRowMinHeight: 64,
        columns: const [
          DataColumn(label: Text('Recipient')),
          DataColumn(label: Text('Pickup')),
          DataColumn(label: Text('Dropoff')),
          DataColumn(label: Text('Fee')),
          DataColumn(label: Text('')),
        ],
        rows: orders
            .map((o) => DataRow(cells: [
                  DataCell(_PersonCell(
                      name: o.recipientName, sub: o.recipientPhone)),
                  DataCell(SizedBox(
                      width: 150,
                      child: Text(o.pickupAddress,
                          overflow: TextOverflow.ellipsis))),
                  DataCell(SizedBox(
                      width: 150,
                      child: Text(o.dropoffAddress,
                          overflow: TextOverflow.ellipsis))),
                  DataCell(Text('${o.fee} MMK',
                      style: const TextStyle(fontWeight: FontWeight.w700))),
                  DataCell(_AssignButton(
                    order: o,
                    enabled: ref
                        .watch(adminDashboardProvider)
                        .activeRiders
                        .isNotEmpty,
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
        color: AdminDesign.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AdminDesign.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: order.isWalkin
                      ? AdminDesign.amberSoft
                      : AdminDesign.blueSoft,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                    order.isWalkin
                        ? Icons.storefront_outlined
                        : Icons.send_outlined,
                    size: 18,
                    color: order.isWalkin
                        ? AdminDesign.amber
                        : AdminDesign.blue),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(order.recipientName,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
              Text('${order.fee} MMK',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, color: AdminDesign.ink)),
            ],
          ),
          Text(order.recipientPhone,
              style: TextStyle(fontSize: 12, color: AdminDesign.inkSoft)),
          const SizedBox(height: 8),
          _LabeledValue(label: 'Pickup', value: order.pickupAddress),
          _LabeledValue(label: 'Dropoff', value: order.dropoffAddress),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: _AssignButton(
              order: order,
              enabled: ref
                  .watch(adminDashboardProvider)
                  .activeRiders
                  .isNotEmpty,
            ),
          ),
        ],
      ),
    );
  }
}

// ===========================================================================
// Shared widgets
// ===========================================================================

class _PersonCell extends StatelessWidget {
  final String name;
  final String sub;
  const _PersonCell({required this.name, required this.sub});
  @override
  Widget build(BuildContext context) => Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          Text(sub,
              style:
                  TextStyle(fontSize: 12, color: AdminDesign.inkSoft)),
        ],
      );
}

class _Avatar extends StatelessWidget {
  final String initials;
  const _Avatar({required this.initials});
  @override
  Widget build(BuildContext context) => Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
              colors: [AdminDesign.indigo, AdminDesign.blue]),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Text(initials,
              style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 13)),
        ),
      );
}

class _ApproveButton extends StatefulWidget {
  final VoidCallback onPressed;
  const _ApproveButton({required this.onPressed});

  @override
  State<_ApproveButton> createState() => _ApproveButtonState();
}

class _ApproveButtonState extends State<_ApproveButton> {
  bool _press = false;
  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: widget.onPressed,
      onTapDown: (_) => setState(() => _press = true),
      onTapUp: (_) => setState(() => _press = false),
      onTapCancel: () => setState(() => _press = false),
      borderRadius: BorderRadius.circular(10),
      child: AnimatedScale(
        scale: _press ? 0.96 : 1,
        duration: const Duration(milliseconds: 110),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
          decoration: BoxDecoration(
            color: AdminDesign.emerald,
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(
                color: AdminDesign.emerald.withValues(alpha: 0.35),
                blurRadius: 10,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: const Text('Approve',
              style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 13)),
        ),
      ),
    );
  }
}

class _RejectButton extends StatefulWidget {
  final VoidCallback onPressed;
  const _RejectButton({required this.onPressed});

  @override
  State<_RejectButton> createState() => _RejectButtonState();
}

class _RejectButtonState extends State<_RejectButton> {
  bool _hover = false;
  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: InkWell(
        onTap: widget.onPressed,
        borderRadius: BorderRadius.circular(10),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 140),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
          decoration: BoxDecoration(
            color: _hover ? AdminDesign.roseSoft : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
                color: _hover ? AdminDesign.rose : const Color(0xFFFECACA)),
          ),
          child: Text('Reject',
              style: TextStyle(
                  color: AdminDesign.rose,
                  fontWeight: FontWeight.w600,
                  fontSize: 13)),
        ),
      ),
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
        backgroundColor: AdminDesign.indigo,
        padding: const EdgeInsets.symmetric(horizontal: 18),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10)),
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
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20)),
        title: const Text('Assign Rider'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Order to ${order.recipientName} (${order.recipientPhone})',
                style: TextStyle(color: AdminDesign.inkSoft, fontSize: 13)),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: selected,
              decoration: InputDecoration(
                labelText: 'Select rider',
                filled: true,
                fillColor: AdminDesign.canvas,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
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
            style: FilledButton.styleFrom(
              backgroundColor: AdminDesign.indigo,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              if (selected != null) {
                ref
                    .read(adminDashboardProvider.notifier)
                    .assignOrder(order.id, selected!);
              }
            },
            child: const Text('Assign'),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  const _StatusChip({required this.label});

  Color get _color {
    final l = label.toLowerCase();
    if (l.contains('approv')) return AdminDesign.emerald;
    if (l.contains('reject')) return AdminDesign.rose;
    if (l.contains('pending')) return AdminDesign.amber;
    return AdminDesign.inkSoft;
  }

  @override
  Widget build(BuildContext context) {
    final c = _color;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(label,
          style: TextStyle(
              color: c, fontSize: 11, fontWeight: FontWeight.w600)),
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
        padding: const EdgeInsets.all(56),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AdminDesign.emeraldSoft,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Icon(icon, size: 44, color: AdminDesign.emerald),
            ),
            const SizedBox(height: 16),
            Text(message,
                style: TextStyle(
                    color: AdminDesign.inkSoft,
                    fontSize: 16,
                    fontWeight: FontWeight.w500)),
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
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AdminDesign.roseSoft,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Icon(Icons.error_outline_rounded,
                  size: 44, color: AdminDesign.rose),
            ),
            const SizedBox(height: 16),
            Text(message,
                textAlign: TextAlign.center,
                style: TextStyle(color: AdminDesign.inkSoft)),
            const SizedBox(height: 16),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: AdminDesign.indigo,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
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
            width: 64,
            child: Text(label,
                style: TextStyle(
                    fontSize: 12,
                    color: AdminDesign.inkSoft,
                    fontWeight: FontWeight.w500)),
          ),
          Expanded(
              child: Text(value,
                  style: const TextStyle(
                      fontSize: 13, color: AdminDesign.ink))),
        ],
      ),
    );
  }
}
