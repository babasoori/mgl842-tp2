data aws_caller_identity current {}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "mgl842_iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "aws_iam_policy_document" "lambda_logs" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:us-east-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.lambda.function_name}:*"]
  }
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda.function_name}"
  retention_in_days = 14
}

resource "aws_iam_policy" "lambda_logs_policy" {
  name        = "lambda_logs_policy"
  description = "Policy for allowing Lambda to create and write to CloudWatch Logs"
  policy      = data.aws_iam_policy_document.lambda_logs.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs_policy_attachment" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logs_policy.arn
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "src/pr_reviewer.py"
  output_path = "src.zip"
}


data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir = "lambda_layer"
  output_path = "lambda_layer.zip"
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename   = "lambda_layer.zip"
  layer_name = "mgl_842_lambda_layer"

  compatible_runtimes = ["python3.12"]

  source_code_hash = data.archive_file.lambda_layer.output_base64sha256
}


resource "aws_lambda_function" "lambda" {
  filename      = "src.zip"
  function_name = "mgl842_lambda_function"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "pr_reviewer.lambda_handler"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.12"

  layers = [aws_lambda_layer_version.lambda_layer.arn]
}
