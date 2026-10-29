# Incremental Stream Codecs

**Reference type:** targeted
**Load when:** A parser or serializer processes partial chunks, framed streams, binary lengths, or bounded decompression.
**Do not load when:** The task uses complete bounded messages without incremental parsing or partial-write decisions.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## State and Framing Decisions

- Bind framing, encoding, byte order, length representation, and malformed-input behavior to the selected format contract.
- Treat transport chunks as arbitrary fragments. One chunk may contain part of a field, several frames, or a frame plus its successor's prefix.
- Preserve parser state and unconsumed bytes across reads. Distinguish a completed item, need-more-input, and invalid input.
- Carry text-decoder state across multibyte boundaries. Decoding each chunk independently can corrupt a valid split character.
- Validate declared lengths before allocation or indexing. Account for arithmetic overflow, remaining input, permitted nesting, and cumulative output.
- Bound varint length and accumulation according to the selected encoding. A missing terminator differs from a valid value awaiting more bytes.
- Distinguish clean EOF at a permitted terminal state from truncation inside a field, character, compressed member, or frame.
- Resume partial writes from the acknowledged offset. Replaying an entire buffer can duplicate a prefix already accepted by the sink.
- Select termination or resynchronization from the protocol contract. Arbitrary byte skipping can invent valid-looking messages after corruption.
- Bound resynchronization work when recovery is supported. A parser loop without input consumption or state progress needs an explicit wait or failure result.
- Limit decompressed output and retained parser state independently of compressed input size.
- Account for memory across active streams and queued output. Backpressure cannot help if parsing accumulates unbounded data before producing an item.

## Distinguishing Cases

| Input or schedule | Observable check |
| --- | --- |
| A multibyte character crosses chunk boundaries | Decoded meaning matches the same valid input delivered together |
| Header, varint, or payload ends mid-frame | EOF reports truncation rather than a clean completed message |
| Declared length exceeds bounds or overflows arithmetic | Rejection occurs before allocation or out-of-bounds access |
| Several frames arrive in one chunk | Each frame is emitted once with the final incomplete suffix retained |
| Sink accepts a prefix, then resumes later | Output contains neither duplicated nor missing bytes |
| Small compressed input expands beyond the output budget | Expansion stops with a defined failure and bounded retained memory |
| Corruption precedes a plausible delimiter | Recovery follows the selected framing rule or terminates explicitly |

Return parser states, EOF semantics, accepted offsets, resource bounds, and recovery limits.
Compare varied chunk partitions against an independent format oracle and explicit malformed-input outcomes.
Keep network delivery guarantees and generic byte-order rules at their existing owners.
