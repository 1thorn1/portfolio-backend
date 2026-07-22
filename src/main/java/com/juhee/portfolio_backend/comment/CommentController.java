package com.juhee.portfolio_backend.comment;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/comments")
public class CommentController {

    private final CommentService commentService;

    @Value("${admin.secret-key}")
    private String adminSecretKey;

    public CommentController(CommentService commentService) {
        this.commentService = commentService;
    }

    @GetMapping
    public List<CommentResponse> getComments() {
        return commentService.getAllComments().stream()
                .map(CommentResponse::from)
                .toList();
    }

    @PostMapping
    public CommentResponse addComment(@Valid @RequestBody CommentRequest request) {
        Comment comment = commentService.addComment(request.author(), request.content());
        return CommentResponse.from(comment);
    }

    @DeleteMapping("/{id}")
    public void deleteComment(@PathVariable Long id, @RequestHeader("X-Admin-Key") String adminKey) {
        if (!adminSecretKey.equals(adminKey)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "관리자만 삭제할 수 있습니다.");
        }
        commentService.deleteComment(id);
    }

    public record CommentRequest(
            @NotBlank @Size(max = 50) String author,
            @NotBlank @Size(max = 1000) String content
    ) {
    }

    public record CommentResponse(Long id, String author, String content, LocalDateTime createdAt) {
        static CommentResponse from(Comment comment) {
            return new CommentResponse(comment.getId(), comment.getAuthor(), comment.getContent(), comment.getCreatedAt());
        }
    }
}
