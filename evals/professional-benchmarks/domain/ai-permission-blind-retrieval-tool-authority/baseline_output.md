# Review

The source application already authenticates users, so we can trust source UI authorization for retrieval. Put all indexed chunks into the common prompt, place retrieved text inside trusted instructions, and let the model invoke tools with ambient service authority. Add a general disclaimer and monitor user feedback after release.
