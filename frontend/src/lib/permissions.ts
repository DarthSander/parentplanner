export type Role = 'owner' | 'partner' | 'caregiver';

const PERMISSIONS: Record<Role, Record<string, boolean>> = {
  owner: {
    view_baby_tasks: true,
    edit_baby_tasks: true,
    view_household_tasks: true,
    edit_household_tasks: true,
    view_private_tasks: true,
    edit_private_tasks: true,
    view_inventory: true,
    edit_inventory: true,
    report_inventory_low: true,
    view_partner_calendar: true,
    manage_members: true,
    manage_settings: true,
    view_patterns: true,
    view_subscription: true,
  },
  partner: {
    view_baby_tasks: true,
    edit_baby_tasks: true,
    view_household_tasks: true,
    edit_household_tasks: true,
    view_private_tasks: false,
    edit_private_tasks: false,
    view_inventory: true,
    edit_inventory: true,
    report_inventory_low: true,
    view_partner_calendar: true,
    manage_members: false,
    manage_settings: false,
    view_patterns: true,
    view_subscription: false,
  },
  caregiver: {
    view_baby_tasks: true,
    edit_baby_tasks: false,
    view_household_tasks: false,
    edit_household_tasks: false,
    view_private_tasks: false,
    edit_private_tasks: false,
    view_inventory: true,
    edit_inventory: false,
    report_inventory_low: true,
    view_partner_calendar: false,
    manage_members: false,
    manage_settings: false,
    view_patterns: false,
    view_subscription: false,
  },
};

export function can(role: Role, permission: string): boolean {
  return PERMISSIONS[role]?.[permission] ?? false;
}
