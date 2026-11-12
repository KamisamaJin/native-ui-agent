# Shared integer transport domain

All immutable input Int fields use the shared signed 32-bit domain supported by
Kotlin Int, Kotlin serialization jsonPrimitive.int, and the Swift input bridge:
-2147483648 through 2147483647.
The JSON schema narrows individual fields further. Existing nonnegative or
positive minima remain, revision is0..2147483647, and portfolioScore remains0..100.
accountBalanceCents explicitly allows the full signed range, including negatives.
Inputs outside fixture.schema.json are outside this component contract.

Revision is an opaque caller-supplied identity key. The component compares it and
never increments it. The published business predicates use comparison, key
equality, and string formatting. They require no sum or product. A producer that
introduces intermediate arithmetic must still preserve those published predicates;
these finite-corpus capability checks claim no arbitrary implementation overflow
proof or universal correctness outside the listed corpus.

Swift uses Bool and Kotlin uses Boolean for schema boolean fields. The final Android
bridge accepts the host's kotlinx.serialization.json.JsonObject and uses its
jsonPrimitive.boolean accessor. Model field values and callback forwarding are
unchanged. The stock theme is explicitly light and non-dynamic for this fixed profile.
This clarification was fixed before any production UI code or native execution.
