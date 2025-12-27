import { sql } from "drizzle-orm";
import { pgTable, text, varchar, date, integer, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export const customers = pgTable("customers", {
  customer_id: varchar("customer_id", { length: 20 }).primaryKey(),
  first_name: varchar("first_name", { length: 100 }).notNull(),
  last_name: varchar("last_name", { length: 100 }).notNull(),
  email: varchar("email", { length: 255 }).notNull(),
  phone_number: varchar("phone_number", { length: 30 }),
  date_of_birth: date("date_of_birth"),
  gender: varchar("gender", { length: 30 }),
  preferred_channel: varchar("preferred_channel", { length: 20 }),
  marketing_opt_in: boolean("marketing_opt_in").default(false),
  vip_flag: boolean("vip_flag").default(false),
  lifetime_value_cents: integer("lifetime_value_cents").default(0),
  avg_order_value_cents: integer("avg_order_value_cents").default(0),
  total_orders: integer("total_orders").default(0),
  preferred_store_id: varchar("preferred_store_id", { length: 20 }),
  notes: text("notes"),
  password: varchar("password", { length: 255 }).notNull().default("password123"),
});

export const insertCustomerSchema = createInsertSchema(customers).omit({});
export type InsertCustomer = z.infer<typeof insertCustomerSchema>;
export type Customer = typeof customers.$inferSelect;

export const customerAddresses = pgTable("customer_addresses", {
  address_id: varchar("address_id", { length: 30 }).primaryKey(),
  customer_id: varchar("customer_id", { length: 20 }).notNull().references(() => customers.customer_id),
  label: varchar("label", { length: 50 }),
  address_line1: varchar("address_line1", { length: 255 }).notNull(),
  address_line2: varchar("address_line2", { length: 255 }),
  city: varchar("city", { length: 100 }).notNull(),
  state: varchar("state", { length: 50 }),
  postal_code: varchar("postal_code", { length: 20 }),
  country: varchar("country", { length: 100 }).default("USA"),
  is_default_shipping: boolean("is_default_shipping").default(false),
  is_default_billing: boolean("is_default_billing").default(false),
});

export const insertCustomerAddressSchema = createInsertSchema(customerAddresses).omit({});
export type InsertCustomerAddress = z.infer<typeof insertCustomerAddressSchema>;
export type CustomerAddress = typeof customerAddresses.$inferSelect;

export const customerPreferences = pgTable("customer_preferences", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  customer_id: varchar("customer_id", { length: 20 }).notNull().references(() => customers.customer_id),
  categories_interested: text("categories_interested"),
  price_sensitivity: varchar("price_sensitivity", { length: 20 }),
  preferred_brands: text("preferred_brands"),
  preferred_styles: text("preferred_styles"),
  preferred_shopping_days: varchar("preferred_shopping_days", { length: 30 }),
});

export const insertCustomerPreferencesSchema = createInsertSchema(customerPreferences).omit({ id: true });
export type InsertCustomerPreferences = z.infer<typeof insertCustomerPreferencesSchema>;
export type CustomerPreferences = typeof customerPreferences.$inferSelect;
