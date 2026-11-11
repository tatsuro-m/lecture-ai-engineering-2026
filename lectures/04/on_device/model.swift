import Foundation
import FoundationModels

struct Request: Decodable {
    let instructions: String
    let prompt: String
    let mode: String
    let steps: [String]
}

let text = DynamicGenerationSchema(type: String.self)
let verdict = DynamicGenerationSchema(name: "Verdict", anyOf: ["pass", "fail", "unsure"])
let criterion = DynamicGenerationSchema(name: "CriterionVerdict", properties: [
    .init(name: "reason", description: "判断の理由を日本語で1〜2文", schema: text),
    .init(name: "verdict", schema: .init(referenceTo: "Verdict"))
])
let judge = DynamicGenerationSchema(name: "JudgeOutput", properties: [
    "grounding", "scope", "hint", "clarity"
].map { .init(name: $0, schema: .init(referenceTo: "CriterionVerdict")) })

do {
    let request = try JSONDecoder().decode(Request.self, from: FileHandle.standardInput.readDataToEndOfFile())
    let nextStep = DynamicGenerationSchema(name: "NextStep", anyOf: request.steps)
    let agent = DynamicGenerationSchema(name: "AgentOutput", properties: [
        .init(name: "step", description: "呼ぶツールの名前。最終回答なら answer", schema: .init(referenceTo: "NextStep")),
        .init(name: "query", description: "search_glossary の検索語", schema: text, isOptional: true),
        .init(name: "lecture", description: "get_lecture_summary / make_quiz の回番号",
              schema: .init(type: Int.self), isOptional: true),
        .init(name: "note", description: "save_learning_log で保存する本文", schema: text, isOptional: true),
        .init(name: "answer", description: "step が answer のときの最終回答", schema: text, isOptional: request.steps.count > 1)
    ])
    let session = LanguageModelSession(model: SystemLanguageModel.default, instructions: request.instructions)
    let schema = try request.mode == "judge"
        ? GenerationSchema(root: judge, dependencies: [criterion, verdict])
        : GenerationSchema(root: agent, dependencies: [nextStep])
    let result = try await session.respond(to: request.prompt, schema: schema, options: GenerationOptions(temperature: 0, maximumResponseTokens: 420))
    print(result.content.jsonString)
} catch {
    FileHandle.standardError.write(Data("\(error)\n".utf8))
    exit(1)
}
