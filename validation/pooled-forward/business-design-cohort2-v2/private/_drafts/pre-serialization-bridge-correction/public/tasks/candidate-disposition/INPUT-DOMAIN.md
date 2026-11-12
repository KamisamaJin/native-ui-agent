# Shared integer transport domain

All immutable input Int fields use the shared signed 32-bit domain supported by
Kotlin Int, Gson asInt, and the Swift input bridge: -2147483648 through2147483647.
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

Swift uses Bool and Kotlin uses Boolean for schema boolean fields. The supplied
bridges already decode booleans accordingly; no bridge or fixture value changed.
This clarification was fixed before any production UI code or native execution.
