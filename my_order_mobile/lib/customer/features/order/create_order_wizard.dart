import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/spacing.dart';
import '../../../core/theme/colors.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/mo_card.dart';
import '../../../core/auth/auth_provider.dart';
import 'order_provider.dart';
import 'order_success_screen.dart';

/// Phase 2 — Customer create-order wizard (P2 -> P8).
///
/// Steps:
///  P2 delivery mode (door_to_door | bus_terminal)
///  P3 pickup location (address + lat/lng; map picker deferred -> manual coords)
///  P4 dropoff (D2D: city/township/address; bus: town/terminal/bus line)
///  P6 recipient name + phone
///  P7 item value + COD + fee payer
///  P8 quote review (calls POST /quotes) -> create order -> P9
class CreateOrderWizard extends ConsumerStatefulWidget {
  const CreateOrderWizard({super.key});

  @override
  ConsumerState<CreateOrderWizard> createState() => _CreateOrderWizardState();
}

class _CreateOrderWizardState extends ConsumerState<CreateOrderWizard> {
  int _step = 0;
  bool _busy = false;
  String? _error;

  // P2
  String _mode = 'door_to_door';

  // P3 pickup
  final _pickupAddress = TextEditingController();
  final _pickupLat = TextEditingController(text: '16.8409');
  final _pickupLng = TextEditingController(text: '96.1735');

  // P4 dropoff
  String _city = 'yangon';
  String? _township;
  List<Map<String, dynamic>> _zones = [];
  bool _zonesLoading = false;
  final _dropoffAddress = TextEditingController();
  final _town = TextEditingController();
  final _terminal = TextEditingController();
  final _busLine = TextEditingController();

  // P6 recipient
  final _recipientName = TextEditingController();
  final _recipientPhone = TextEditingController();

  // P7 item/payment
  final _itemValue = TextEditingController();
  final _codAmount = TextEditingController();
  String _feePayer = 'sender';

  // P8 result
  Map<String, dynamic>? _quote;

  final List<String> _steps = const [
    'Delivery mode',
    'Pickup',
    'Dropoff',
    'Recipient',
    'Item & payment',
    'Review',
  ];

  @override
  void initState() {
    super.initState();
    _loadZones();
  }

  @override
  void dispose() {
    for (final c in [
      _pickupAddress,
      _pickupLat,
      _pickupLng,
      _dropoffAddress,
      _town,
      _terminal,
      _busLine,
      _recipientName,
      _recipientPhone,
      _itemValue,
      _codAmount,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadZones() async {
    if (_zones.isNotEmpty) return;
    setState(() => _zonesLoading = true);
    try {
      final zones = await ref.read(orderApiProvider).listZones();
      setState(() {
        _zones = zones;
        _zonesLoading = false;
      });
    } on OrderApiException catch (e) {
      setState(() {
        _zonesLoading = false;
        _error = e.message;
      });
    }
  }

  List<String> get _townshipsForCity {
    final city = _city;
    return _zones
        .where((z) => (z['city'] as String).toLowerCase() == city)
        .map((z) => z['township'] as String)
        .toList()
      ..sort();
  }

  Map<String, dynamic> _buildQuotePayload() {
    final isD2D = _mode == 'door_to_door';
    return {
      'delivery_mode': _mode,
      'fee_payer': _feePayer,
      if (isD2D) ...{
        'destination_city': _city,
        'destination_township': _township?.trim() ?? '',
        'dropoff_address': _dropoffAddress.text.trim(),
        'dropoff_lat': double.tryParse(_pickupLat.text) ?? 16.8409,
        'dropoff_lng': double.tryParse(_pickupLng.text) ?? 96.1735,
      } else ...{
        'destination_town': _town.text.trim(),
        'terminal_name': _terminal.text.trim(),
        'bus_line': _busLine.text.trim(),
      },
    };
  }

  Future<void> _fetchQuote() async {
    setState(() => _busy = true);
    try {
      final quote = await ref.read(orderApiProvider).requestQuote(_buildQuotePayload());
      setState(() {
        _quote = quote;
        _busy = false;
        _error = null;
        _step = 5; // review
      });
    } on OrderApiException catch (e) {
      setState(() => _error = e.message);
      _busy = false;
    }
  }

  Future<void> _createOrder() async {
    if (_quote == null) return;
    setState(() => _busy = true);
    try {
      final itemVal = double.tryParse(_itemValue.text) ?? 0;
      final cod = double.tryParse(_codAmount.text) ?? 0;
      final maximum = num.tryParse(_quote!['maximum_fee_mmk'].toString()) ?? 0.0;
      final order = await ref.read(orderApiProvider).createOrder({
        'quote_id': _quote!['id'],
        'recipient_name': _recipientName.text.trim(),
        'recipient_phone': _recipientPhone.text.trim(),
        'pickup_address': _pickupAddress.text.trim(),
        'pickup_lat': double.tryParse(_pickupLat.text) ?? 16.8409,
        'pickup_lng': double.tryParse(_pickupLng.text) ?? 96.1735,
        'item_value': itemVal,
        'cod_amount': cod,
        'authorized_max_fee_mmk': maximum, // authorize the max up front
        'terms_accepted': true,
      });
      if (!mounted) return;
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => OrderSuccessScreen(order: order, mode: _mode),
        ),
      );
    } on OrderApiException catch (e) {
      setState(() => _error = e.message);
      _busy = false;
    }
  }

  void _next() {
    setState(() => _error = null);
    if (_step < 4) {
      setState(() => _step++);
    } else if (_step == 4) {
      _fetchQuote();
    }
  }

  void _back() {
    setState(() => _error = null);
    if (_step == 0) {
      Navigator.of(context).pop();
    } else {
      setState(() => _step--);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('New Order'),
        leading: IconButton(icon: const Icon(Icons.close), onPressed: _back),
      ),
      body: SafeArea(
        child: Column(
          children: [
            _Stepper(current: _step, total: _steps.length, labels: _steps),
            if (_error != null)
              Container(
                margin: const EdgeInsets.all(MOSpacing.md),
                padding: const EdgeInsets.all(MOSpacing.md),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded,
                        color: theme.colorScheme.error),
                    const SizedBox(width: MOSpacing.sm),
                    Expanded(
                      child: Text(_error!,
                          style: TextStyle(color: theme.colorScheme.error)),
                    ),
                  ],
                ),
              ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(MOSpacing.lg),
                child: _stepBody(),
              ),
            ),
            _Footer(
              busy: _busy,
              isReview: _step == 5,
              onBack: _back,
              onNext: _step == 5 ? _createOrder : _next,
              nextLabel: _step == 4
                  ? 'Get quote'
                  : _step == 5
                      ? 'Confirm & create'
                      : 'Continue',
            ),
          ],
        ),
      ),
    );
  }

  Widget _stepBody() {
    switch (_step) {
      case 0:
        return _ModeStep(mode: _mode, onChanged: (v) => setState(() => _mode = v));
      case 1:
        return _PickupStep(
          address: _pickupAddress,
          lat: _pickupLat,
          lng: _pickupLng,
        );
      case 2:
        return _mode == 'door_to_door'
            ? _DropoffD2DStep(
                city: _city,
                onCity: (v) {
                  setState(() {
                    _city = v ?? 'yangon';
                    _township = null;
                  });
                  _loadZones();
                },
                townships: _townshipsForCity,
                township: _township,
                onTownship: (v) => setState(() => _township = v),
                loading: _zonesLoading,
                address: _dropoffAddress,
              )
            : _DropoffBusStep(
                town: _town,
                terminal: _terminal,
                busLine: _busLine,
              );
      case 3:
        return _RecipientStep(name: _recipientName, phone: _recipientPhone);
      case 4:
        final isPartner = ref.watch(authProvider).profile?.isActivePartner ?? false;
        return _ItemPaymentStep(
          itemValue: _itemValue,
          codAmount: _codAmount,
          feePayer: _feePayer,
          onFeePayer: (v) => setState(() => _feePayer = v ?? 'sender'),
          mode: _mode,
          isPartner: isPartner,
        );
      case 5:
        return _ReviewStep(quote: _quote, mode: _mode);
      default:
        return const SizedBox.shrink();
    }
  }
}

/// Horizontal stepper indicator.
class _Stepper extends StatelessWidget {
  final int current;
  final int total;
  final List<String> labels;
  const _Stepper(
      {required this.current, required this.total, required this.labels});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      height: 56,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: MOSpacing.lg),
        itemCount: total,
        separatorBuilder: (_, _) => const SizedBox(width: MOSpacing.sm),
        itemBuilder: (_, i) {
          final active = i == current;
          final done = i < current;
          final color = done || active
              ? MOColors.senderColor
              : theme.colorScheme.outline;
          return Row(
            children: [
              CircleAvatar(
                radius: 13,
                backgroundColor: color,
                child: Text('${i + 1}',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 6),
              Text(labels[i],
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: active ? theme.colorScheme.primary : theme.hintColor,
                    fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                  )),
            ],
          );
        },
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  final bool busy;
  final bool isReview;
  final VoidCallback onBack;
  final VoidCallback onNext;
  final String nextLabel;
  const _Footer({
    required this.busy,
    required this.isReview,
    required this.onBack,
    required this.onNext,
    required this.nextLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(MOSpacing.lg),
      child: Row(
        children: [
          if (!isReview)
            TextButton(onPressed: onBack, child: const Text('Back')),
          const SizedBox(width: MOSpacing.sm),
          Expanded(
            child: FilledButton(
              onPressed: busy ? null : onNext,
              style: FilledButton.styleFrom(
                backgroundColor: MOColors.senderColor,
                minimumSize: const Size.fromHeight(52),
              ),
              child: busy
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : Text(nextLabel),
            ),
          ),
        ],
      ),
    );
  }
}

// --- Steps ---------------------------------------------------------------

class _ModeStep extends StatelessWidget {
  final String mode;
  final ValueChanged<String> onChanged;
  const _ModeStep({required this.mode, required this.onChanged});

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('How would you like to send?',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: MOSpacing.lg),
          _ModeCard(
            selected: mode == 'door_to_door',
            icon: Icons.door_front_door_outlined,
            title: 'Door to Door',
            subtitle: 'We pick up and deliver to the address',
            onTap: () => onChanged('door_to_door'),
          ),
          const SizedBox(height: MOSpacing.md),
          _ModeCard(
            selected: mode == 'bus_terminal',
            icon: Icons.directions_bus_outlined,
            title: 'Bus Terminal',
            subtitle: 'Drop at a bus terminal for inter-city',
            onTap: () => onChanged('bus_terminal'),
          ),
        ],
      );
}

class _ModeCard extends StatelessWidget {
  final bool selected;
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const _ModeCard({
    required this.selected,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return MOCard(
      onTap: onTap,
      padding: const EdgeInsets.all(MOSpacing.lg),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: selected
                  ? MOColors.senderColor.withValues(alpha: 0.15)
                  : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon,
                color: selected ? MOColors.senderColor : theme.hintColor),
          ),
          const SizedBox(width: MOSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: theme.textTheme.titleMedium),
                Text(subtitle, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
          if (selected)
            const Icon(Icons.check_circle, color: MOColors.senderColor),
        ],
      ),
    );
  }
}

class _PickupStep extends StatelessWidget {
  final TextEditingController address;
  final TextEditingController lat;
  final TextEditingController lng;
  const _PickupStep(
      {required this.address, required this.lat, required this.lng});

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Pickup location',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: MOSpacing.lg),
          _Field(label: 'Pickup address', controller: address),
          const SizedBox(height: MOSpacing.md),
          Row(
            children: [
              Expanded(
                  child: _Field(
                      label: 'Latitude', controller: lat, keyboard: TextInputType.number)),
              const SizedBox(width: MOSpacing.md),
              Expanded(
                  child: _Field(
                      label: 'Longitude',
                      controller: lng,
                      keyboard: TextInputType.number)),
            ],
          ),
          const SizedBox(height: MOSpacing.sm),
          Text('Map picker coming soon — coordinates prefilled to Yangon.',
              style: Theme.of(context).textTheme.bodySmall),
        ],
      );
}

class _DropoffD2DStep extends StatelessWidget {
  final String city;
  final ValueChanged<String?> onCity;
  final List<String> townships;
  final String? township;
  final ValueChanged<String?> onTownship;
  final bool loading;
  final TextEditingController address;
  const _DropoffD2DStep({
    required this.city,
    required this.onCity,
    required this.townships,
    required this.township,
    required this.onTownship,
    this.loading = false,
    required this.address,
  });

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Dropoff (Door to Door)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: MOSpacing.lg),
          DropdownButtonFormField<String>(
            initialValue: city,
            decoration: const InputDecoration(labelText: 'City'),
            items: const [
              DropdownMenuItem(value: 'yangon', child: Text('Yangon')),
              DropdownMenuItem(value: 'mandalay', child: Text('Mandalay')),
            ],
            onChanged: onCity,
          ),
          const SizedBox(height: MOSpacing.md),
          if (loading)
            const LinearProgressIndicator()
          else
            DropdownButtonFormField<String>(
              initialValue: township,
              decoration: const InputDecoration(labelText: 'Township'),
              hint: const Text('Select township'),
              items: townships
                  .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                  .toList(),
              onChanged: onTownship,
            ),
          const SizedBox(height: MOSpacing.md),
          _Field(label: 'Dropoff address', controller: address),
        ],
      );
}

class _DropoffBusStep extends StatelessWidget {
  final TextEditingController town;
  final TextEditingController terminal;
  final TextEditingController busLine;
  const _DropoffBusStep({
    required this.town,
    required this.terminal,
    required this.busLine,
  });

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Dropoff (Bus Terminal)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: MOSpacing.lg),
          _Field(label: 'Destination town', controller: town),
          const SizedBox(height: MOSpacing.md),
          _Field(label: 'Terminal name', controller: terminal),
          const SizedBox(height: MOSpacing.md),
          _Field(label: 'Bus line', controller: busLine),
        ],
      );
}

class _RecipientStep extends StatelessWidget {
  final TextEditingController name;
  final TextEditingController phone;
  const _RecipientStep({required this.name, required this.phone});

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Recipient details',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: MOSpacing.lg),
          _Field(label: 'Recipient name', controller: name),
          const SizedBox(height: MOSpacing.md),
          _Field(
            label: 'Recipient phone',
            controller: phone,
            keyboard: TextInputType.phone,
            hint: '09xxxxxxxxx',
          ),
        ],
      );
}

class _ItemPaymentStep extends StatelessWidget {
  final TextEditingController itemValue;
  final TextEditingController codAmount;
  final String feePayer;
  final ValueChanged<String?> onFeePayer;
  final String mode;
  final bool isPartner;
  const _ItemPaymentStep({
    required this.itemValue,
    required this.codAmount,
    required this.feePayer,
    required this.onFeePayer,
    required this.mode,
    this.isPartner = false,
  });

  @override
  Widget build(BuildContext context) {
    final showPartnerFields = mode == 'door_to_door' && isPartner;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('Item & payment',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: MOSpacing.lg),
        _Field(
          label: 'Item value (MMK)',
          controller: itemValue,
          keyboard: TextInputType.number,
          hint: 'e.g. 50000',
        ),
        if (showPartnerFields) ...[
          const SizedBox(height: MOSpacing.md),
          _Field(
            label: 'COD amount (MMK) — 0 if none',
            controller: codAmount,
            keyboard: TextInputType.number,
            hint: '0',
          ),
          const SizedBox(height: MOSpacing.md),
          DropdownButtonFormField<String>(
            initialValue: feePayer,
            decoration: const InputDecoration(labelText: 'Who pays the fee?'),
            items: const [
              DropdownMenuItem(value: 'sender', child: Text('Sender (me)')),
              DropdownMenuItem(
                  value: 'recipient', child: Text('Recipient')),
            ],
            onChanged: onFeePayer,
          ),
        ] else if (mode == 'bus_terminal') ...[
          const SizedBox(height: MOSpacing.md),
          Container(
            padding: const EdgeInsets.all(MOSpacing.md),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
                'Cash on delivery is not available for Bus Terminal orders.',
                style: TextStyle(fontSize: 13)),
          ),
        ],
      ],
    );
  }
}

class _ReviewStep extends StatelessWidget {
  final Map<String, dynamic>? quote;
  final String mode;
  const _ReviewStep({required this.quote, required this.mode});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (quote == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final base = num.tryParse(quote!['base_fee_mmk'].toString()) ?? 0.0;
    final zone = num.tryParse(quote!['zone_surcharge_mmk'].toString()) ?? 0.0;
    final disc = num.tryParse(quote!['partner_discount_mmk'].toString()) ?? 0.0;
    final est = num.tryParse(quote!['estimated_fee_mmk'].toString()) ?? 0.0;
    final max = num.tryParse(quote!['maximum_fee_mmk'].toString()) ?? 0.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('Review your quote',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: MOSpacing.lg),
        MOCard(
          child: Column(
            children: [
              _Row(label: 'Delivery mode',
                  value: mode == 'door_to_door' ? 'Door to Door' : 'Bus Terminal'),
              _Row(label: 'Base fee', value: Formatters.mmk(base)),
              if (zone > 0) _Row(label: 'Zone surcharge', value: Formatters.mmk(zone)),
              if (disc > 0)
                _Row(
                    label: 'Partner discount',
                    value: '- ${Formatters.mmk(disc)}',
                    color: MOColors.senderColor),
              const Divider(height: MOSpacing.lg),
              _Row(
                label: 'Estimated fee',
                value: Formatters.mmk(est),
                bold: true,
              ),
              _Row(
                label: 'Max (if oversized)',
                value: Formatters.mmk(max),
                color: theme.hintColor,
              ),
            ],
          ),
        ),
        const SizedBox(height: MOSpacing.md),
        Text(
          'Quote valid for 30 minutes. Tap confirm to create the order.',
          style: theme.textTheme.bodySmall,
        ),
      ],
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;
  final Color? color;
  const _Row({required this.label, required this.value, this.bold = false, this.color});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: MOSpacing.xs),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: Theme.of(context).textTheme.bodyMedium),
            Text(
              value,
              style: (bold
                      ? Theme.of(context).textTheme.titleMedium
                      : Theme.of(context).textTheme.bodyMedium)
                  ?.copyWith(
                fontWeight: bold ? FontWeight.w700 : FontWeight.normal,
                color: color,
              ),
            ),
          ],
        ),
      );
}

/// Reusable labelled text field.
class _Field extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final TextInputType? keyboard;
  final String? hint;
  const _Field({
    required this.label,
    required this.controller,
    this.keyboard,
    this.hint,
  });

  @override
  Widget build(BuildContext context) => TextField(
        controller: controller,
        keyboardType: keyboard,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: const OutlineInputBorder(),
        ),
      );
}
