# Writeup: mrGraph

## Challenge Overview
**Challenge Name**: mrGraph
**Type**: Web / GraphQL
**Goal**: Khai thác lỗ hổng trong GraphQL API để tìm bài viết ẩn chứa flag.

## Bước 1: Reconnaissance (Thu thập thông tin)

Trang web là một blog đơn giản. Kiểm tra mã nguồn hoặc network request, ta thấy trang web giao tiếp với backend thông qua endpoint `/graphql`.

Gửi thử một query cơ bản để xác nhận:
```graphql
query {
  __typename
}
```
Kết quả trả về hợp lệ, xác nhận đây là GraphQL.

## Bước 2: Introspection (Liệt kê cấu trúc)

GraphQL thường hỗ trợ tính năng Introspection cho phép client xem cấu trúc dữ liệu (Schema). Sử dụng query sau để liệt kê các Types và Fields:

```graphql
query {
  __schema {
    types {
      name
      fields {
        name
      }
    }
  }
}
```

Kết quả trả về schema có Type tên là `Post` với các trường đáng chú ý:
- `id`
- `title`
- `content`
- `isHidden`: Gợi ý về các bài viết bị ẩn.
- `postPassword`: Gợi ý về cơ chế bảo vệ bài viết.

## Bước 3: Khai thác (Exploitation)

Ban đầu, tôi thử query tất cả các bài viết (`allPosts`), nhưng chỉ nhận được các bài viết công khai (public).

Dựa vào việc có trường `id`, tôi thử query trực tiếp từng bài viết cụ thể (IDOR - Insecure Direct Object Reference) để xem có thể truy cập bài viết ẩn không.

Query khai thác:
```graphql
query {
  post(id: 4) {
    id
    title
    content
    isHidden
    postPassword
  }
}
```

Tại `id: 4` (một ID không xuất hiện trong danh sách `allPosts`), server trả về nội dung của bài viết ẩn mà không cần xác thực phức tạp (hoặc cơ chế `postPassword` bị lộ ngay trong query).

## Kết quả

Trong nội dung (`content`) hoặc `postPassword` của bài viết có ID 4, ta tìm thấy Flag.

**Flag:**
`VSL{y0u_r34lly_kn0w_4b0u7_6r4ph_d0n7_y4}`
